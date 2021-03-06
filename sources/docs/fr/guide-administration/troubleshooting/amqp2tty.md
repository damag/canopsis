# Analyse temps réel des flux issus des connecteurs ou des relais AMQP

La commande `amqp2tty` permet de se connecter en ligne de commande sur l'exchange `canopsis.events` et ainsi d'afficher les évènements bruts qui circulent.

La commande affiche les résultats sur le canal d'erreur, si vous souhaitez rechercher des évènements particuliers, il faut rediriger `stderr` vers la sortie standard.

Voici un exemple d'utilisation de la commande. Elle doit être exécutée depuis un nœud Canopsis, idéalement en étant connecté avec l'utilisateur `canopsis` :
```shell
$ /opt/canopsis/bin/amqp2tty 2>&1 | grep -i centreon
```

et son résultat :
```json
{
    "connector": "centreon",
    "connector_name": "centreoninstance1",
    "event_type": "check",
    "source_type": "component",
    "component": "test_composant",
    "address": "x.x.x.x",
    "output": "(Process Timeout)",
    "state": 1,
    "state_type": 1,
    "scheduled": true,
    "check_type": 0,
    "current_attempt": 1,
    "max_attempts": 5,
    "execution_time": 9.544648,
    "latency": 0.597,
    "command_name": "/usr/lib64/nagios/plugins/check_icmp -H x.x.x.x -w 3000.0,80% -c 5000.0,100% -p 1",
    "component_alias": "alias composant",
    "hostgroups": ["HG1"],
    "timestamp": 1528812075
}
```
