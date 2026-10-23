// Testes locais: mocks da API de datasets. Nenhuma conexao ao Fluig ou a internet.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../fluig/dsFornecedoresHomologados.js"), "utf8");
const rows = JSON.parse(fs.readFileSync(path.join(__dirname, "../fornecedores.json"), "utf8"));
let call;
const context = {
    ConstraintType: { MUST: 1 },
    DatasetFactory: {
        createConstraint: (fieldName, initialValue, finalValue, constraintType) => ({fieldName, initialValue, finalValue, constraintType}),
        getDataset: (name, fields, constraints, sortFields) => {
            call = {name, fields, constraints, sortFields};
            // Representa o simples: encaminha o parametro para o filtro da origem.
            return {values: rows.filter(row => String(row.homologado) === constraints[0].initialValue)};
        }
    }
};
vm.createContext(context);
vm.runInContext(source, context);
const result = context.createDataset(null, null, null);
assert.equal(call.name, "dsFornecedores");
assert.equal(call.constraints.length, 1);
assert.equal(call.constraints[0].fieldName, "homologado");
assert.equal(call.constraints[0].initialValue, "true");
assert.equal(call.constraints[0].finalValue, "true");
assert.equal(call.constraints[0].constraintType, context.ConstraintType.MUST);
assert.equal(result.values.length, 10);
assert.ok(result.values.every(row => row.homologado === true));
context.DatasetFactory.getDataset = () => null;
assert.throws(() => context.createDataset(null, null, null), /dsFornecedores.*retornou null/);
console.log("Dataset avancado: constraint homologado=true/MUST, nome da origem, retorno e diagnostico null: OK");
