# -*- coding: utf-8 -*-

"""Module in chage of defining the graph context and updating
 it when it's needed."""

from __future__ import unicode_literals

from canopsis.task.core import register_task
from canopsis.context_graph.manager import ContextGraph


context_graph_manager = ContextGraph()


ids_cache = set()

LOGGER = None


def update_cache():
    global cache
    cache = context_graph_manager.get_all_entities()


def create_entity(
        id,
        name,
        etype,
        depends=[],
        impact=[],
        measurements=[],
        infos={}):
    return {'_id': id,
            'type': etype,
            'name': name,
            'depends': depends,
            'impact': impact,
            'measurements': measurements,
            'infos': infos
            }


def check_type(entities, expected):
    """Raise TypeError if the type of the entities entities does not match
    the expected type.
    :param entities: the entities to check.
    :param expected: the expected type.
    :raises TypeError: if the entity does not match the expected one."""
    if entities["type"] != expected:
        raise TypeError("Entities {0} does not match {1}".format(
            entities["_id"], expected))
    return True


def update_depends_links(ent_from, ent_to):
    """Update the links depends from ent_from to ent_to. Basicaly, append
    the id of ent_to on the the "depends" of ent_from.
    :param ent_from: the entities that will be updated
    :param ent_to: the entities which id will be used to update ent_from"""
    if ent_to["_id"] not in ent_from["depends"]:
        ent_from["depends"].append(ent_to["_id"])


def update_impact_links(ent_from, ent_to):
    """Update the links impact from ent_from to ent_to. Basicaly, append
    the id of ent_to on the the "impact" of ent_from.
    :ent_from: the entities that will be updated
    :ent_to: the entities which id will be used to update :ent_from:"""
    if ent_to["_id"] not in ent_from["impact"]:
        ent_from["impact"].append(ent_to["_id"])


def update_links_conn_res(conn, res):
    """Update depends and impact links between the conn connector and the
    res resource. Raise a TypeError if conn is not a connector and/or res
    is not a resource.
    :param conn: the connector to update
    :param res: the resource to update
    :raises TypeError: if the entities does not match the expected one."""
    check_type(conn, "connector")
    check_type(res, "resource")

    update_depends_links(conn, res)
    update_impact_links(res, conn)


def update_links_conn_comp(conn, comp):
    """Update depends and impact links between the conn connector and the
    comp component. Raise a TypeError if conn is not a connector and/or comp
    is not a component.
    :param conn: the connector to update
    :param comp: the component to update
    :raises TypeError: if the entities does not match the expected one."""
    check_type(conn, "connector")
    check_type(comp, "component")

    update_depends_links(conn, comp)
    update_impact_links(comp, conn)


def update_links_res_comp(res, comp):
    """Update depends and impact links between the res resource and the
    comp component. Raise a TypeError if res is not a resource and/or comp
    is not a component.
    :param res: the resource to update
    :param comp: the component to update
    :raises TypeError: if the entities does not match the expected one."""
    check_type(res, "resource")
    check_type(comp, "component")

    update_depends_links(res, comp)
    update_impact_links(comp, res)


def determine_presence(ids, data):
    """Determine if the ids are in data. If the ids is present in data, the
    element of the tuple that show the presence of the ids will be set to True.
    False otherwise. If the ids given is set to None, the matching element will
    be set to None.
    :param ids: a set of dict of ids
    :param data: a set of ids
    :return: a tuple of boolean of None following pattern
    (connector presence, component presence, resource presence).

    .. note :: currently an only a resource can be None in an canopsis event.
    """

    conn_here = ids['conn_id'] in data
    comp_here = ids['comp_id'] in data

    if ids['res_id'] is not None:
        res_here = ids['res_id'] in data
    else:
        res_here = None

    return (conn_here, comp_here, res_here)


def add_missing_ids(presence, ids):
    """Update the cache"""
    if presence[0] == False:  # Update connector
        cache.add(ids["conn_id"])

    if presence[1] == False:  # Update component
        cache.add(ids["comp_id"])

    if presence[2] == False:  # Update resource
        cache.add(ids["res_id"])


def update_case1(entities, ids):
    """Case 1 update entities"""

    LOGGER.debug("Case 1.")

    comp_there = False
    re_there = False
    conn_there = False
    comp_pos = re_pos = conn_pos = -1

    for k, i in enumerate(entities):
        if i['type'] == 'component':
            comp_there = True
            comp_pos = k
        elif i['type'] == 'resource':
            re_there = True
            re_pos = k
        elif i['type'] == 'connector':
            conn_there = True
            conn_pos = k

    if conn_there:
        LOGGER.debug(
            "Connector {0} present in database".format(ids["conn_id"]))
        if comp_there:
            LOGGER.debug(
                "Component {0} present in database".format(ids["comp_id"]))
            if not re_there:
                LOGGER.debug(
                    "Resource {0} not present in database".format(
                        ids["re_id"]))
                re = create_entity(ids['re_id'],
                                   ids['re_id'],
                                   'resource',
                                   impact=[],
                                   depends=[])
                update_links_conn_res(entities[conn_pos], re)
                update_links_res_comp(re, entities[conn_pos])
                entities.append(re)
                context_graph_manager.put_entities(entities)
                # put re + update
        else:
            LOGGER.debug(
                "Component {0} not present in database".format(ids["comp_id"]))
            # push comp + put re + update conn
            comp = create_entity(ids['comp_id'],
                                 ids['comp_id'],
                                 'component',
                                 depends=[ids['comp_id']])
            re = create_entity(ids['re_id'],
                               ids['re_id'],
                               'resource',
                               impact=[ids['comp_id']])
            update_links_conn_res(entities[conn_pos], re)
            update_links_conn_comp(entities[conn_pos], comp)
            entities.append(comp)
            entities.append(re)
            context_graph_manager.put_entities(entities)
    else:
        LOGGER.debug(
            "Connector {0} not present in database".format(ids["conn_id"]))
        if comp_there:
            LOGGER.debug(
                "Component {0} present in database".format(ids["comp_id"]))
            if re_there:
                LOGGER.debug(
                    "Resource {0} present in database".format(ids["re_id"]))
                # put connector + updates comp re
                conn = create_entity(ids['conn_id'],
                                     ids['conn_id'],
                                     'connector')
                update_links_conn_res(conn, entities[re_pos])
                update_links_conn_comp(conn, entities[comp_pos])
                entities.append(conn)
                context_graph_manager.put_entities(entities)
            else:
                LOGGER.debug(
                    "Resource {0} not present in database".format(
                        ids["re_id"]))
                # put connector + put re + update comp
                conn = create_entity(ids['conn_id'],
                                     ids['conn_id'],
                                     'connector',
                                     impact=[ids['re_id']])
                re = create_entity(ids['re_id'],
                                   ids['re_id'],
                                   'resource',
                                   depends=[ids['conn_id']])
                update_links_res_comp(re, entities[comp_pos])
                update_links_conn_comp(conn, entities[comp_pos])
                entities.append(conn)
                entities.append(re)
                context_graph_manager.put_entities(entities)
        else:
            LOGGER.debug(
                "Component {0} not present in database".format(ids["comp_id"]))
            # put comp + put re + put conn
            comp = create_entity(ids['comp_id'],
                                 ids['comp_id'],
                                 'component',
                                 depends=[ids['re_id'], ids['conn_id']],
                                 impact=[])
            re = create_entity(ids['re_id'],
                               ids['re_id'],
                               'resource',
                               impact=[ids['comp_id']],
                               depends=[ids['conn_id']])
            conn = create_entity(ids['conn_id'],
                                 ids['conn_id'],
                                 'connector',
                                 impact=[ids['comp_id'], ids['re_id']],
                                 depends=[])
            context_graph_manager.put_entities([comp, re, conn])
    LOGGER.debug("Entities : {0}".format(entities))


def update_case2(entities, ids):
    """Case 2 update entities"""

    LOGGER.debug("Case 2")

    comp_there = False
    re_there = False
    comp_pos = conn_pos = -1
    for k, i in enumerate(entities):
        if i['type'] == 'component':
            comp_there = True
            comp_pos = k
        elif i['type'] == 'resource':
            re_there = True
        elif i['type'] == 'connector':
            conn_pos = k

    if comp_there:
        LOGGER.debug(
            "Component {0} present in database".format(ids["comp_id"]))
        if not re_there:
            LOGGER.debug(
                "Resource {0} not present in database".format(ids["re_id"]))
            # insert re + maj comp depends + maj conn impact
            re = create_entity(ids['re_id'], ids['re_id'], 'resource')
            update_links_conn_res(entities[conn_pos], re)
            update_links_res_comp(re, entities[comp_pos])
            entities.append(re)
            context_graph_manager.put_entities(entities)
        else:
            LOGGER.debug(
                "Resource {0} present in database. Do nothing".format(
                    ids["re_id"]))
    else:
        LOGGER.debug(
            "Component {0} not present in database".format(ids["comp_id"]))
        # insert comp + insert re + maj conn impact with com and re
        comp = create_entity(ids['comp_id'],
                             ids['comp_id'],
                             'component',
                             depends=[ids['comp_id']])
        re = create_entity(ids['re_id'],
                           ids['re_id'],
                           'resource',
                           impact=[ids['comp_id']])
        update_links_conn_res(entities[conn_pos], re)
        update_links_conn_comp(entities[conn_pos], comp)
        entities.append(comp)
        entities.append(re)
        context_graph_manager.put_entities(entities)
        LOGGER.debug("Entities : {0}".format(entities))


def update_case3(entities, ids):
    """Case 3 update entities"""
    LOGGER.debug("Case 3")

    re_there = False
    for i, k in enumerate(entities):
        if k['type'] == 'resource':
            re_there = True
        if k['type'] == "component":
            comp_pos = i
        if k['type'] == "connector":
            conn_pos = i

    if not re_there:
        LOGGER.debug(
            "Resource {0} not present in datase.".format(ids["re_id"]))
        # push re + update conn impact + update comp depends
        re = create_entity(ids["re_id"], ids["re_id"], "resource")
        entities.append(re)
        update_links_conn_res(entities[conn_pos], re)
        update_links_res_comp(re, entities[comp_pos])
        LOGGER.debug("Entities : {0}".format(entities))
        context_graph_manager.put_entities(entities)
        return 0
    return 1


def update_case4(entities, ids):
    """Case 4 update entities"""
    LOGGER.debug("Case 4 : nothing to do here.")


def update_case5(entities, ids):
    """Case 5 update entities"""

    LOGGER.debug("Case 5")

    conn_there = False
    re_there = False

    for i, k in enumerate(entities):
        if k['type'] == 'connector':
            conn_there = True
            conn_pos = i
        if k['type'] == 'resource':
            re_there = True
            re_pos = i
        if k['type'] == 'component':
            comp_pos = i

    if conn_there:
        LOGGER.debug(
            "Connector {0} present in database.".format(ids['conn_id']))
        if re_there:
            LOGGER.debug(
                "Resource {0} present in database.".format(ids['re_id']))
            return
        else:
            LOGGER.debug(
                "Resource {0} not present in database.".format(ids['re_id']))
            # put re + update comp depends + update conn impact
            re = create_entity(ids["re_id"],
                               ids["re_id"],
                               "resource",
                               [ids["conn_id"]],
                               [ids["comp_id"]])
            update_links_res_comp(re, entities[comp_pos])
            update_links_conn_res(entities[conn_pos], re)
            entities.append(re)
    else:
        LOGGER.debug(
            "Connector {0} not present in database.".format(ids['conn_id']))

        conn = create_entity(ids["conn_id"],
                             ids["conn_id"],
                             "connector")
        entities.append(conn)
        if re_there:
            LOGGER.debug(
                "Resource {0} present in database.".format(ids['re_id']))
            # put conn + maj impac in conn + update re depends
            update_links_conn_comp(conn, entities[comp_pos])
            update_links_conn_res(conn, entities[re_pos])
        else:
            # put conn + put re + update conn impact for comp and re
            LOGGER.debug(
                "Resource {0} not present in database.".format(ids['re_id']))
            re = create_entity(ids["re_id"],
                               ids["re_id"],
                               "resource",
                               [ids["conn_id"]],
                               [ids["comp_id"]])
            update_links_res_comp(re, entities[comp_pos])
            update_links_conn_res(conn, re)
            update_links_conn_comp(conn, entities[comp_pos])
            entities.append(re)
    LOGGER.debug("Entities : {0}".format(entities))
    context_graph_manager.put_entities(entities)


def update_case6(entities, ids):
    """Case 6 update entities"""
    LOGGER.debug("Case 6.")

    conn_there = False
    res_pos = comp_pos = -1

    for k, i in enumerate(entities):
        if i['_id'] == ids['conn_id']:
            conn_there = True
            return 0
        if i['type'] == 'component':
            comp_pos = k
        if i['type'] == 'resource':
            res_pos = k

    if not conn_there:
        LOGGER.debug(
            "Connector {0} not present in database.".format(ids['conn_id']))
        conn = create_entity(
            ids['conn_id'],
            ids['conn_id'],
            "connector")
        update_links_conn_res(conn, entities[res_pos])
        update_links_conn_comp(conn, entities[comp_pos])
        entities.append(conn)
        LOGGER.debug("Entities : {0}".format(entities))
        context_graph_manager.put_entities(entities)
        return 1


def update_context(presence, ids):
    if presence == (False, False, False) or presence == (False, False, None):
        # Case 1
        pass

    elif presence == (True, False, False) or presence == (True, False, None):
        # Case 2
        pass

    elif presence == (True, True, False):
        # Case 3
        pass

    elif presence == (True, True, True):
        # Case 4
        pass

    elif presence == (False, True, False) or presence == (False, True, None):
        # Case 5
        pass

    elif presence == (False, True, True) or presence == (False, True, None):
        # Case 6
        pass

    else:
        LOGGER.warning(
            "No case for the given presence : {0} and ids {1}".format(presence, ids))
        raise ValueError("No case for the given ids and data.")


def gen_ids(event):
    ret_val = {
        'comp_id': '{0}'.format(event['component']),
        're_id': None,
        'conn_id': '{0}/{1}'.format(event['connector'], event['connector_name'])
    }
    if 'resource' in event.keys():
        ret_val['re_id'] = '{0}/{1}'.format(event['resource'],
                                            event['component'])
    return ret_val


@register_task
def event_processing(
        engine, event, manager=None, logger=None, ctx=None, tm=None, cm=None,
        **kwargs
):
    """event_processing

    :param engine:
    :param event:
    :param manager:
    :param logger:
    :param ctx:
    :param tm:
    :param cm:
    :param **kwargs:
    """

    global LOGGER
    LOGGER = logger

    ids = gen_ids(event)

    presence = determine_presence(ids, cache)

    if presence == (True, True, True) or (True, True, None):
        # Everything is in cache, so we skip
        return None

    add_missing_ids(presence, ids)

    entites_in_db = context_graph_manager.get_entity(ids.values())
    data = set() 
    for i in entites_in_db:
        data.add(i['_id'])
    presence = determine_presence(ids, data)
    if presence == (True, True, True) or (True, True, None):
        # Everything is in cache, so we skip
        return None
    update_context(presence, entities_in_db)

    LOGGER.debug("*** The end. ***")


@register_task
def beat(engine, logger=None, **kwargs):
    update_cache()
