# Enrichissement dynamique du context-graph

Canopsis 2.3 accepte des champs personnalisés dans l'objet event, permettant de donner du contexte à un évènement. On peut par exemple envoyer un HostGroup, une adresse IP, etc. 

Ce contexte est ensuite utilisable deans les bacs à évènements.

Dans Canopsis 2.5, ces informations ne sont pas reprises dans le modèle entité/alarmes, ce qui rend obligatoire l'intégration et la synchronisation d'une CMDB pour recréer ce contexte autour de l'alarme. Cette opération est parfois trop complexe par rapport aux informations qu'il est nécessaire d'intégrer. 

Le but de cette évolution est de restaurer un comportement similaire à celui de Canopsis 2.3, intégré dans le modèle du context-graph.

## Objectif de l'évolution

> En tant qu'administrateur de Canopsis, je veux que les informations personnalisées envoyées dans un évènement soient utilisables dans Canopsis, afin de les utiliser dans les différentes vues du logiciel. 

## Définition fonctionnelle

- l'évènement accepte un dictionnaire nommé "infos", pouvant accueillir des informations administratives sur le contexte d'un évènement (HostGroup, Adresse IP, Nom d'hôte/Alias de l'hôte, etc.)

- lorsqu'un évènement arrive dans Canopsis, chaque champ non standard est lu, et intégré dans le dictionnaire "infos" de l'objet évènement

- Lorsque cet évènement enrichi arrive dans le gestionnaire de contexte, celui-ci insère les données du champ infos de l'évènement dans l'entité du contexte correspondante.

## Discussion technique
