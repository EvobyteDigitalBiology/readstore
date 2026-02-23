#!/usr/bin/env nextflow

params.readstore_dataset = "tumor_normal_rep_1"
params.index = "$projectDir/index/salmon_index"
params.outdir = "results"

process GET_READSTORE_FASTQ {

    input:
    val readstore_dataset
    
    output:
    tuple env(read_1_path), env(read_2_path)

    script:
    """
    read_1_path=\$(readstore dataset get --name $readstore_dataset --read1-path)
    read_2_path=\$(readstore dataset get --name $readstore_dataset --read2-path)
    """
}

process QUANTIFICATION {
    
    cpus 4

    publishDir params.outdir, mode:'copy'

    input:
    val readstore_dataset
    path salmon_index
    path reads

    output:
    path "$readstore_dataset"

    script:
    """
    salmon quant --threads $task.cpus --libType=U -i $salmon_index -1 ${reads[0]} -2 ${reads[1]} -o $readstore_dataset
    """
}

process UPLOAD_QUANT_RESULTS {

    input:
    val readstore_dataset
    path quant_results

    script:
    """
    readstore pro-data upload --dataset-name $readstore_dataset --name tx_quantification -t salmon "$quant_results/quant.sf"
    """
}

workflow {
    reads_ch = GET_READSTORE_FASTQ(params.readstore_dataset)
    quant_ch = QUANTIFICATION(params.readstore_dataset, params.index, reads_ch)
    UPLOAD_QUANT_RESULTS(params.readstore_dataset, quant_ch)
}