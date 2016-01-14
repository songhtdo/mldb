# This file is part of MLDB. Copyright 2015 Datacratic. All rights reserved.


import json

dataset_config = {
    'type'    : 'sparse.mutable',
    'id'      : 'example'
}

dataset = mldb.create_dataset(dataset_config)

dataset.record_row("r1", [["person", "nick", 0],
                          ["thing", "appl", 0],
                          ["has", 1, 0]])
dataset.record_row("r2", [["person", "nick", 0],
                          ["thing", "goog", 0],
                          ["has", 2, 0]])
dataset.record_row("r3", [["person", "francois", 0],
                          ["thing", "appl", 0],
                          ["has", 3, 0]])
dataset.record_row("r4", [["person", "francois", 0],
                          ["thing", "tsla", 0],
                          ["has", 4, 0]])

mldb.log("Committing dataset")
dataset.commit()

result = mldb.perform('GET', '/v1/query', [['q', 'select pivot(thing, has) as * from example group by person']])

mldb.log(result)

rez = mldb.perform("PUT", "/v1/procedures/dataset_creator", [], 
    {
        "type": "transform",
        "params": {
            "inputData": "select pivot(thing, has) as * from example group by person",
            "outputDataset": { "id": "example2", "type":"sparse.mutable" }
        }
    })

mldb.log(rez)

rez = mldb.perform("POST", "/v1/procedures/dataset_creator/runs")
mldb.log(rez)

result = mldb.perform('GET', '/v1/query', [['q', 'select * from example2']])

mldb.log(result)

assert result['statusCode'] == 200
row = json.loads(result['response'])[0]
assert row['columns'][0][0] == "tsla" or row['columns'][0][0] == "appl"

#MLDB-914

dataset_config = {
    'type'    : 'sparse.mutable',
    'id'      : 'example3'
}

dataset2 = mldb.create_dataset(dataset_config)

dataset2.record_row("r1", [["person", "nick", 0],
                          ["thing", "appl", 0],
                          ["has", 1, 0]])
dataset2.record_row("r2", [["person", "nick", 0],
                          ["thing", "goog", 0],
                          ["has", 2, 0]])
dataset2.record_row("r3", [["person", "françois", 0],
                          ["thing", "appl", 0],
                          ["has", 3, 0]])
dataset2.record_row("r4", [["person", "françois", 0],
                          ["thing", "tsla", 0],
                          ["has", 4, 0]])

mldb.log("Committing dataset")
dataset2.commit()

result = mldb.perform('GET', '/v1/query', [['q', 'select count(*) from example3 group by person']])

mldb.log(result)

assert result['statusCode'] == 200
assert json.loads(result['response'])[0]['rowName'] == unicode('["françois"]',encoding='utf-8'), 'failed non-ascii support'
assert json.loads(result['response'])[1]['rowName'] == unicode('["nick"]',encoding='utf-8'), 'failed non-ascii support'

mldb.script.set_return("success")
