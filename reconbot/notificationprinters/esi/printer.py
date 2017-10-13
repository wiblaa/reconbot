import abc
import datetime
import yaml

class Printer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, eve):
        self.eve = eve

    def transform(self, notification):
        text = self.get_notification_text(notification)
        timestamp = self.timestamp_to_date(notification['timestamp'])

        return '[%s] %s' % (timestamp, text)

    def get_notification_text(self, notification):
        text = yaml.load(notification['text'])

        types = {
            'AllWarDeclaredMsg': self.corporation_war_declared,
            'EntosisCaptureStarted': self.entosis_capture_started,
            'SovCommandNodeEventStarted': self.sov_structure_command_nodes_decloaked,
            'SovStructureDestroyed': self.sov_structure_destroyed,
            'SovStructureReinforced': self.sov_structure_reinforced,
            'StructureUnderAttack': self.citadel_attacked,
            'OwnershipTransferred': self.structure_transferred,
            'StructureOnline': self.citadel_onlined,
            'StructureFuelAlert': self.citadel_low_fuel,
            'StructureAnchoring': self.citadel_anchored,
            'StructureUnanchoring': self.citadel_unanchored,
            'StructureServicesOffline': self.citadel_out_of_fuel,
            'StructureLostShields': self.citadel_reinforced,
            'TowerAlertMsg': self.pos_attack,
            'StationServiceEnabled': self.entosis_enabled_structure,
            'StationServiceDisabled': self.entosis_disabled_structure,
            'OrbitalReinforced': self.customs_office_reinforced,
            'OrbitalAttacked': self.customs_office_attacked,
            'SovAllClaimAquiredMsg': self.sov_claim_acquired,
            'SovStationEnteredFreeport': self.sov_structure_freeported,
            'AllAnchoringMsg': self.structure_anchoring_alert,
            'InfrastructureHubBillAboutToExpire': self.ihub_bill_about_to_expire,
            'SovAllClaimLostMsg': self.sov_claim_lost,
            'SovStructureSelfDestructRequested': self.sov_structure_started_self_destructing,
            'SovStructureSelfDestructFinished': self.sov_structure_self_destructed,
            'StationConquerMsg': self.station_conquered
        }

        if notification['type'] in types:
            return types[notification['type']](text)

        return 'Unknown notification type for printing'

    def corporation_war_declared(self, notification):
        try:
            against_corp = self.get_corporation(notification['againstID'])
        except:
            against_corp = self.get_alliance(notification['againstID'])
        try:
            declared_by_corp = self.get_corporation(notification['declaredByID'])
        except:
            declared_by_corp = self.get_alliance(notification['declaredByID'])

        return 'War has been declared to %s by %s' % (against_corp, declared_by_corp)

    # 41
    def sov_claim_lost(self, notification):
        owner = self.get_corporation(notification['corpID'])
        system = self.get_system(notification['solarSystemID'])

        return 'SOV lost in %s by %s' % (system, owner)

    # 43
    def sov_claim_acquired(self, notification):
        owner = self.get_corporation(notification['corpID'])
        system = self.get_system(notification['solarSystemID'])

        return 'SOV acquired in %s by %s' % (system, owner)

    # 45
    def pos_anchoring_alert(self, notification):
        owner = self.get_corporation(notification['corpID'])
        moon = self.eve.get_moon(notification['moonID'])

        return 'New POS anchored in "%s" by %s' % (moon['name'], owner)

    # 75
    def pos_attack(self, notification):
        moon = self.eve.get_moon(notification['moonID'])
        attacker = self.get_character(notification['aggressorID'])
        item_type = self.get_item(notification['typeID'])

        return "%s POS \"%s\" (%.1f%% shield, %.1f%% armor, %.1f%% hull) under attack by %s" % (
            moon['name'],
            item_type,
            notification['shieldValue']*100,
            notification['armorValue']*100,
            notification['hullValue']*100,
            attacker
        )

    # 79
    def station_conquered(self, notification):
        system = self.get_system(notification['solarSystemID'])
        old_owner = self.get_corporation(notification['oldOwnerID'])
        new_owner = self.get_corporation(notification['newOwnerID'])

        return "Station conquered from %s by %s in %s" % (old_owner, new_owner, system)

    # 93 - poco attacked
    def customs_office_attacked(self, notification):
        attacker = self.get_character(notification['aggressorID'])
        planet = self.get_planet(notification['planetID'])
        shields = int(notification['shieldLevel']*100)

        return "\"%s\" POCO (%d%% shields) has been attacked by %s" % (planet, shields, attacker)

    # 94 - poco reinforced
    def customs_office_reinforced(self, notification):
        attacker = self.get_character(notification['aggressorID'])
        planet = self.get_planet(notification['planetID'])
        timestamp = self.eve_timestamp_to_date(notification['reinforceExitTime'])

        return "\"%s\" POCO has been reinforced by %s (comes out of reinforce on \"%s\")" % (planet, attacker, timestamp)

    # 95 - structure (not necessarily POCO) transferred
    def structure_transferred(self, notification):
        from_corporation = self.get_corporation(notification['fromCorporationLinkData'][-1])
        to_corporation = self.get_corporation(notification['toCorporationLinkData'][-1])
        structure = notification['structureName']
        system = self.get_system(notification['solarSystemLinkData'][-1])
        character = self.get_character(notification['characterLinkData'][-1])

        return "\"%s\" structure in %s has been transferred from %s to %s by %s" % (
            structure,
            system,
            from_corporation,
            to_corporation,
            character
        )

    # 147 - entosis capture started
    def entosis_capture_started(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure = self.get_item(notification['structureTypeID'])

        return "Capturing of \"%s\" in %s has started" % (structure, system)

    # 148 - entosis has enabled structure
    def entosis_enabled_structure(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure = self.get_item(notification['structureTypeID'])

        return "Structure \"%s\" in %s has been enabled" % (structure, system)

    # 149 - entosis has disabled structure
    def entosis_disabled_structure(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure = self.get_item(notification['structureTypeID'])

        return "Structure \"%s\" in %s has been disabled" % (structure, system)

    # 160 - SOV structure reinforced
    def sov_structure_reinforced(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure_type = self.get_campaign_event_type(notification['campaignEventType'])
        timestamp = self.eve_timestamp_to_date(notification['decloakTime'])

        return "SOV structure \"%s\" in %s has been reinforced, nodes will decloak \"%s\"" % (structure_type, system, timestamp)

    # 161 - SOV structure command nodes decloaked
    def sov_structure_command_nodes_decloaked(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure_type = self.get_campaign_event_type(notification['campaignEventType'])

        return "Command nodes for \"%s\" SOV structure in %s have decloaked" % (structure_type, system)

    # 162 - SOV Structure has been destroyed
    def sov_structure_destroyed(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure_type = self.get_item(notification['structureTypeID'])

        return "SOV structure \"%s\" in %s has been destroyed" % (structure_type, system)

    # 163 - SOV Structure has been freeported
    def sov_structure_freeported(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure_type = self.get_item(notification['structureTypeID'])
        timestamp = self.eve_timestamp_to_date(notification['freeportexittime'])

        return "SOV structure \"%s\" in %s has been freeported, exits freeport on \"%s\"" % (structure_type, system, timestamp)

    # 181 - Citadel low fuel
    def citadel_low_fuel(self, notification):
        print(notification)
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") low fuel alert in %s" % (
            citadel_type,
            citadel_name,
            system)

    # 182 - Citadel anchoring alert
    def citadel_anchored(self, notification):
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        corp = self.get_corporation(notification['ownerCorpLinkData'][-1])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") anchored in %s by %s" % (
            citadel_type,
            citadel_name,
            system,
            corp)

    def citadel_unanchored(self, notification):
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        corp = self.get_corporation(notification['ownerCorpLinkData'][-1])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") unanchored in %s by %s" % (
            citadel_type,
            citadel_name,
            system,
            corp)


    # 184 - Citadel attacked
    def citadel_attacked(self, notification):
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        attacker = self.get_character(notification['charID'])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") attacked (%.1f%% shield, %.1f%% armor, %.1f%% hull) in %s by %s" % (
            citadel_type,
            citadel_name,
            notification['shieldPercentage'],
            notification['armorPercentage'],
            notification['hullPercentage'],
            system,
            attacker)

    # 185 - Citadel onlined
    def citadel_onlined(self, notification):
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") onlined in %s" % (
            citadel_type,
            citadel_name,
            system)

    # 186 - Citadel reinforced
    def citadel_reinforced(self, notification):
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        citadel_name = self.get_structure_name(notification['structureID'])
        timestamp = self.eve_duration_to_date(notification['timeLeft'])

        return "Citadel (%s, \"%s\") reinforced in %s (comes out of reinforce on \"%s\")" % (
            citadel_type,
            citadel_name,
            system,
            timestamp)

    # 188 - Citadel destroyed
    def citadel_destroyed(self, notification):
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        system = self.get_system(notification['solarsystemID'])
        corp = self.get_corporation(notification['ownerCorpLinkData'][-1])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") destroyed in %s owned by %s" % (
            citadel_type,
            citadel_name,
            system,
            corp)

    # 198 - Citadel ran out of fuel
    def citadel_out_of_fuel(self, notification):
        system = self.get_system(notification['solarsystemID'])
        citadel_type = self.get_item(notification['structureShowInfoData'][1])
        services = map(lambda ID: self.get_item(ID), notification['listOfServiceModuleIDs'])
        citadel_name = self.get_structure_name(notification['structureID'])

        return "Citadel (%s, \"%s\") ran out of fuel in %s with services \"%s\"" % (
            citadel_type,
            citadel_name,
            system,
            ', '.join(services))

    def structure_anchoring_alert(self, notification):
        owner = self.get_corporation(notification['corpID'])
        moon = self.eve.get_moon(notification['moonID'])
        item_type = self.get_item(notification['typeID'])

        return 'New structure (%s) anchored in "%s" by %s' % (item_type, moon['name'], owner)

    def ihub_bill_about_to_expire(self, notification):
        corp = self.get_corporation(notification['corpID'])
        due_date = self.eve_timestamp_to_date(notification['dueDate'])
        system = self.get_system(notification['solarSystemID'])

        return 'IHUB bill to %s for system %s will expire %s' % (corp, system, due_date)

    def sov_structure_self_destructed(self, notification):
        system = self.get_system(notification['solarSystemID'])
        structure = self.get_item(notification['structureTypeID'])

        return 'SOV structure "%s" has self destructed in %s' % (structure, system)

    def sov_structure_started_self_destructing(self, notification):
        character = self.get_character(notification['charID'])
        end_time = self.eve_timestamp_to_date(notification['destructTime'])
        system = self.get_system(notification['solarSystemID'])
        item = self.get_item(notification['structureTypeID'])

        return 'Self-destruction of "%s" SOV structure in %s has been requested by %s. Structure will self-destruct on "%s"' % (item, system, character, end_time)


    @abc.abstractmethod
    def get_corporation(self, corporation_id):
        return

    @abc.abstractmethod
    def get_alliance(self, alliance_id):
        return

    def get_item(self, item_id):
        item = self.eve.get_item(item_id)
        return item['name']

    @abc.abstractmethod
    def get_system(self, system_id):
        return

    def get_planet(self, planet_id):
        planet = self.eve.get_planet(planet_id)
        system = self.get_system(planet['system_id'])
        return '%s in %s' % (planet['name'], system)

    @abc.abstractmethod
    def get_character(self, character_id):
        return

    def get_campaign_event_type(self, event_type):
        if event_type == 1:
            return 'TCU'
        elif event_type == 2:
            return 'IHUB'
        elif event_type == 3:
            return 'Station'
        else:
            return 'Unknown structure type "%d"' % event_type

    def get_structure_name(self, structure_id):
        structure = self.eve.get_structure(structure_id)
        if 'name' in structure:
            return structure['name']
        else:
            return "Unknown name"

    def timestamp_to_date(self, timestamp):
        return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d %H:%M:%S')

    def eve_timestamp_to_date(self, microseconds):
        """
        Convert microsoft epoch to unix epoch
        Based on: http://www.wiki.eve-id.net/APIv2_Char_NotificationTexts_XML
        """

        seconds = microseconds/10000000 - 11644473600
        return datetime.datetime.utcfromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')

    def eve_duration_to_date(self, microseconds):
        """
        Convert microsoft epoch to unix epoch
        Based on: http://www.wiki.eve-id.net/APIv2_Char_NotificationTexts_XML
        """

        seconds = microseconds/10000000
        timedelta = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        return timedelta.strftime('%Y-%m-%d %H:%M:%S')

