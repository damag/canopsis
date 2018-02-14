# Blackouts de Masse

## User story

> En tant qu'utilisateur, je peux filtrer un périmètre donné afin d'éliminer l'affichage des alarmes quand tout le périmètre est tombe (perte interconnection, supervision down, etc.)

## Définition fonctionnelle

- l'utilisateur ouvre l'explorateur d'entités et sélectionne les entités à filtrer

- il clique sur "Ajouter un pbehavior" et programme le créneau pendant lequel le blackout doit être actif

- il valide, les alarmes sont filtrées et aucune nouvelle alarme ne sera visible sur les entités concernées pendant la période de blackout (couverte par le pbehavior)

## Discussion technique