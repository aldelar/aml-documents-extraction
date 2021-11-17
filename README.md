# aml-documents-extraction

Cognitive Search service is a very popular tool for enterprise customers to quick retreive searchable insights. It is an all-in-one solution with powerful indexing/search capabilities, Search + UI (KMA deployment), and lots of out of the box skills to just turn on.

![Cognitive Search](/doc/cognitive-search.png)

However, often times, enterprise customers find the solution is hard to be customized, especially when they only need one or two components but with requirements of more granular controls.

Azure ML was originally designed as an orchestration with ability to pull in ML/AI activities as modules. AML with batch processing gives user full control of each enrichment step ( environment / compute / scale out) with more capabilities:
-	A skill is just one python script (usually running as an AzureML ParallelRunStep to control scale out)
-	Natural steppingstone when eventually in need for custom ML models as skills
-	Scheduling and blob triggers also available in AML
-	The pattern can also be applied to non AI/ML workloads

![Azure ML](/doc/azure-ml.png)

Flexibilities go with extra efforts:
-	Requires to build up on top of the metadata store if need search, but could also deploy KMA on top of Cosmos DB
-	Lots of steps to ‘re-code’ if you need all Cognitive Search features

An example of how to user Azure ML with barch processing:

![Azure ML](/doc/aml-documents-extraction-pipeline.png)

In this example, you can see the following steps and modules:

-	pdf-to-png: ‘pdf2image’ python lib
-	document-classification: Custom Vision model
-	form-metadata-extraction: FormRecognizer / Microsoft Bing Spellcheck (‘pyspellchecker’ python lib + curated domain specific dictionary)
-	Cosmos DB tracks metadata across steps up to final per document full metadata record.
-	Units of work from step to step are passed as jar file (jar may contain some intermediate artifacts as json + actual work items).

Each step uses a slightly different compute image and compute and scale out configuration, and the solution is deployable as a pipeline web service.