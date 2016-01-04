# This file is part of MLDB. Copyright 2015 Datacratic. All rights reserved.


import datetime, json, random

raw_text = "All Good Things... comprises the 25th and 26th episodes of the seventh season and the series finale of the syndicated American science fiction television series Star Trek: The Next Generation. It is the 177th and 178th episodes of the series overall. The title is derived from the expression All good things must come to an end, a phrase used by the character Q during the episode itself. The finale was written as a valentine to the show's fans, and is now generally regarded as one of the series' best episodes.".split(" ")

dataset_config = {
    'type'    : 'sparse.mutable',
    'id'      : 'toy'
}

dataset = mldb.create_dataset(dataset_config)
mldb.log("data loader created dataset")

now = datetime.datetime.now()

for i in xrange(200):
    words = [[raw_text[random.randint(0, len(raw_text)-1)], 1, now] for x in xrange(25)]
    words.append(["LABEL", "true" if i % 2 == 0 else "false", now])
    dataset.record_row("example-%d" % i, words)

mldb.log("Committing dataset")
dataset.commit()


###########
# add feature gen function
script_func_conf = {
    "id":"featHasher",
    "type":"experimental.feature_generator.hashed_column",
    "params": {
        "numBits": 5
    }
}
script_func_output = mldb.perform("PUT", "/v1/functions/" + script_func_conf["id"], [], 
                                    script_func_conf)
mldb.log("The resulf of the script function creation " + json.dumps(script_func_output))
assert script_func_output["statusCode"] < 400
mldb.log("passed assert")


###########
### create features dataset
rez = mldb.perform("PUT", "/v1/procedures/dataset_creator", [], 
    {
        "type": "transform",
        "params": {
            "inputData": { 
                "select" :  "{ featHasher({{* EXCLUDING(LABEL)} as columns})[hash] } as features, LABEL",
                "from" : { "id": "toy" }
            },
            "outputDataset": { "id": "toy_feats", "type":"sparse.mutable" }
        }
    })
mldb.log(rez)
assert rez["statusCode"] < 400

rez = mldb.perform("POST", "/v1/procedures/dataset_creator/runs")
mldb.log(rez)
assert rez["statusCode"] < 400


############
### train a cls
rez = mldb.perform("PUT", "/v1/procedures/tng_classif", [], {
        "type": "classifier.train",
        "params": {
            "trainingData": {
                "where": "rowHash() % 3 != 1",
                "select": "{* EXCLUDING(LABEL)} as features, LABEL = 'true' as label",
                "from" : { "id": "toy_feats" }
            },
            "configuration": {
                "glz": {
                    "type": "glz",
                    "verbosity": 3,
                    "normalize": True,
                    "ridge_regression": True
                }
            },
            "algorithm": "glz",
            "modelFileUrl": "file://models/tng.cls"
        }
    })

mldb.log(rez)

rez = mldb.perform("POST", "/v1/procedures/tng_classif/runs")
mldb.log(rez)
assert rez["statusCode"] < 400



##########
## now test it

rez = mldb.perform("PUT", "/v1/functions/tng_scorer", [], {
    "type": "classifier",
    "params": { "modelFileUrl": "file://models/tng.cls" }
})
mldb.log(rez)
assert rez["statusCode"] < 400

score_sql = """
tng_scorer({{ * EXCLUDING(LABEL)} as features})[score]
"""
rez = mldb.perform("PUT", "/v1/procedures/tng_score_proc", [], {
    "type": "classifier.test",
    "params": {
        "testingData": "select {*} as features, LABEL = 'true' as label, " + score_sql + " as score from toy_feats where rowHash() % 3 = 1",
        "outputDataset": { "id":"toy_cls_baseline_scorer_rez", "type": "sparse.mutable" }
    }
})
rez = mldb.perform("POST", "/v1/procedures/tng_score_proc/runs")
mldb.log(rez)
assert rez["statusCode"] < 400

mldb.log(json.loads(rez["response"])["status"]["auc"])

mldb.script.set_return("success")




