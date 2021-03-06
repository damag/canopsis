# Implémentation de sources de données

Une source de données externe est un module go exportant une variable
`DataSourceFactory` qui implémente l'interface `DataSourceFactory` (définie
dans
`git.canopsis.net/canopsis/go-revolution/lib/canopsis/eventfilter/data_source.go`).

Les plugins sont compilés avec `go build -buildmode=plugin`, qui crée un
fichier `.so`. Ils doivent être recompilés à chaque version de Canopsis.

Le code ci-dessous est un exemple minimal d'un plugin qui renvoie toujours les
même données :

```go
package main

import (
	"fmt"
	"strings"

	"git.canopsis.net/canopsis/go-revolution/lib/canopsis/eventfilter"
)

type dummyDataSourceFactory struct{}

// Create est appelé lors du décodage des règles. Cette méthode lit les
// paramètres de la source de données, et renvoie un objet implémentant
// l'interface eventfilter.DataSourceGetter.
func (f dummyDataSourceFactory) Create(parameters map[string]interface{}) (eventfilter.DataSourceGetter, error) {
	if len(parameters) != 0 {
		unexpectedParameters := make([]string, 0, len(parameters))
		for key := range parameters {
			unexpectedParameters = append(unexpectedParameters, key)
		}
		return nil, fmt.Errorf("unexpected parameters for entity data source: %s", strings.Join(unexpectedParameters, ", "))
	}

	return dummyDataSourceGetter{}, nil
}

type dummyDataSourceGetter struct {}

// Get est appelé à l'exécution de la règle contenant la source de donnée, et
// renvoie les données correspondant à l'événement, qui est disponible dans
// parameters.Event.
func (g dummyDataSourceGetter) Get(parameters eventfilter.DataSourceGetterParameters) (interface{}, error) {
	result := map[string]interface{}{
		"test": "testvalue",
	}
	return result, nil
}

var DataSourceFactory dummyDataSourceFactory
```
