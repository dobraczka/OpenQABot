from SPARQLWrapper import SPARQLWrapper, JSON

def getInfo(r):
    print type(r)
    jsonObject = r.json()
    resultList = []
    for i in jsonObject:
         sparql = SPARQLWrapper("http://dbpedia.org/sparql")
         sparql.setQuery("""
                     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                     PREFIX dbo: <http://dbpedia.org/ontology/>
                     SELECT DISTINCT ?label ?abstract ?thumbnail
                     WHERE { <%s> rdfs:label ?label .
                            OPTIONAL{<%s> dbo:abstract ?abstract FILTER(LANG(?abstract)='en') } .
                            OPTIONAL{<%s> dbo:thumbnail ?thumbnail}
                     FILTER(LANG(?label)='en')
                     }

         """ % (i['URI_PARAM'], i['URI_PARAM'], i['URI_PARAM']))
         sparql.setReturnFormat(JSON)
         results = sparql.query().convert()
         print "SPARQL RESULT \n"
         print results
         resultList.append(results)
    return resultList

