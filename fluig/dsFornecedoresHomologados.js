/**
 * Publicar como dataset AVANCADO: dsFornecedoresHomologados.
 * Requer um dataset SIMPLES publicado com codigo exato dsFornecedores.
 * Esse simples deve consultar GET /fornecedores, com homologado vazio.
 */
function createDataset(fields, constraints, sortFields) {
    var nomeDatasetSimples = "dsFornecedores";

    // ===== INICIO DO FILTRO: SOMENTE FORNECEDORES HOMOLOGADOS =====
    var filtroHomologado = DatasetFactory.createConstraint(
        "homologado",
        "true",
        "true",
        ConstraintType.MUST
    );
    // ===== FIM DO FILTRO =====

    var origem = DatasetFactory.getDataset(
        nomeDatasetSimples,
        null,
        [filtroHomologado],
        null
    );

    if (origem == null) {
        throw "A consulta ao dataset '" + nomeDatasetSimples +
            "' retornou null. Confira o codigo, a publicacao e a consulta direta do dataset simples.";
    }

    // O simples interpreta a constraint e chama /fornecedores?homologado=true.
    // A API filtra na origem e o avancado devolve o dataset recebido.
    return origem;
}
