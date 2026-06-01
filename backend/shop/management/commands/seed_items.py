"""
Management command to seed Dota 2 items
"""
from django.core.management.base import BaseCommand
from shop.models import Dota2Item

IMG = '/images/items'

ITEMS = [
    # ---- Core items ----
    {
        'name': "Aghanim's Scepter",
        'description': "Upgrades the ultimate of most heroes. +10 to all attributes, +175 Health, +175 Mana.",
        'gold_cost': 4200,
        'usd_price': 24.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/ultimate_scepter.png',
    },
    {
        'name': 'Black King Bar',
        'description': "+10 Strength, +24 Damage. Active: Grants spell immunity for 6-9 seconds.",
        'gold_cost': 4050,
        'usd_price': 22.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/black_king_bar.png',
    },
    {
        'name': 'Blink Dagger',
        'description': "Teleport to a target point up to 1200 units away.",
        'gold_cost': 2250,
        'usd_price': 12.99,
        'rarity': 'rare',
        'category': 'core',
        'image_url': f'{IMG}/blink.png',
    },
    {
        'name': 'Daedalus',
        'description': "+88 Damage. Critical strike: 225% damage.",
        'gold_cost': 5150,
        'usd_price': 28.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/lesser_crit.png',
    },
    {
        'name': 'Butterfly',
        'description': "+35 Agility, +30 Attack Speed, +35% Evasion.",
        'gold_cost': 5450,
        'usd_price': 29.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/butterfly.png',
    },
    {
        'name': 'Heart of Tarrasque',
        'description': "+45 Strength, +250 Health. Provides health regeneration.",
        'gold_cost': 5200,
        'usd_price': 27.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/heart.png',
    },
    {
        'name': 'Assault Cuirass',
        'description': "+35 Attack Speed, +10 Armor. Aura: -5 armor to enemies.",
        'gold_cost': 5125,
        'usd_price': 26.99,
        'rarity': 'rare',
        'category': 'core',
        'image_url': f'{IMG}/assault.png',
    },
    {
        'name': 'Desolator',
        'description': "+50 Damage. Attacks reduce enemy armor by -6 for 7 seconds.",
        'gold_cost': 3500,
        'usd_price': 18.99,
        'rarity': 'rare',
        'category': 'core',
        'image_url': f'{IMG}/desolator.png',
    },
    {
        'name': 'Manta Style',
        'description': "+26 Agility, +12 Attack Speed. Creates 2 illusions of your hero.",
        'gold_cost': 4600,
        'usd_price': 25.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/manta.png',
    },
    {
        'name': 'Satanic',
        'description': "+25 Strength, +25 Damage. Active: 200% lifesteal for 6 seconds.",
        'gold_cost': 5050,
        'usd_price': 27.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/satanic.png',
    },
    {
        'name': 'Divine Rapier',
        'description': "+330 Damage. Drops on death. The ultimate risk-reward item.",
        'gold_cost': 6000,
        'usd_price': 49.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/rapier.png',
    },
    {
        'name': 'Monkey King Bar',
        'description': "+40 Damage, +45 Attack Speed. 75% chance to pierce evasion.",
        'gold_cost': 4975,
        'usd_price': 26.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/monkey_king_bar.png',
    },
    {
        'name': 'Eye of Skadi',
        'description': "+22 All Attributes, +220 Health, +220 Mana. Slows enemies on attack.",
        'gold_cost': 5300,
        'usd_price': 29.99,
        'rarity': 'legendary',
        'category': 'core',
        'image_url': f'{IMG}/skadi.png',
    },
    {
        'name': 'Power Treads',
        'description': "+25 Move Speed, +45 Attack Speed. Can switch between +10 STR/AGI/INT.",
        'gold_cost': 1400,
        'usd_price': 8.99,
        'rarity': 'uncommon',
        'category': 'core',
        'image_url': f'{IMG}/power_treads.png',
    },
    {
        'name': 'Phase Boots',
        'description': "+18 Damage, +45 Move Speed. Active: Phase through units, +20% MS.",
        'gold_cost': 1500,
        'usd_price': 9.99,
        'rarity': 'uncommon',
        'category': 'core',
        'image_url': f'{IMG}/phase_boots.png',
    },
    # ---- Support items ----
    {
        'name': 'Force Staff',
        'description': "+10 Intelligence, +4 HP Regen. Pushes any target unit 600 units in the direction it is facing.",
        'gold_cost': 2250,
        'usd_price': 13.99,
        'rarity': 'rare',
        'category': 'support',
        'image_url': f'{IMG}/force_staff.png',
    },
    {
        'name': 'Scythe of Vyse',
        'description': "Transforms an enemy into a harmless beast for 3.5 seconds.",
        'gold_cost': 5650,
        'usd_price': 32.99,
        'rarity': 'legendary',
        'category': 'support',
        'image_url': f'{IMG}/sheepstick.png',
    },
    {
        'name': 'Refresher Orb',
        'description': "+13 HP Regen, +7 Mana Regen. Active: Resets all ability and item cooldowns.",
        'gold_cost': 5000,
        'usd_price': 28.99,
        'rarity': 'rare',
        'category': 'support',
        'image_url': f'{IMG}/refresher.png',
    },
    # ---- Neutral items ----
    {
        'name': 'Magic Stick',
        'description': "Instantly restores 15 HP and 15 MP per charge stored. Max 10 charges.",
        'gold_cost': 200,
        'usd_price': 2.99,
        'rarity': 'uncommon',
        'category': 'neutral',
        'image_url': f'{IMG}/magic_stick.png',
    },
    # ---- Consumables ----
    {
        'name': 'Observer Ward',
        'description': "Places a ward that grants vision of the surrounding area.",
        'gold_cost': 75,
        'usd_price': 0.99,
        'rarity': 'common',
        'category': 'consumable',
        'image_url': f'{IMG}/ward_observer.png',
    },
    {
        'name': 'Sentry Ward',
        'description': "Places a ward that detects invisible units in a 1000 radius.",
        'gold_cost': 75,
        'usd_price': 0.99,
        'rarity': 'common',
        'category': 'consumable',
        'image_url': f'{IMG}/ward_sentry.png',
    },
    {
        'name': 'Tango',
        'description': "Consume a tree to restore 115 HP over 16 seconds.",
        'gold_cost': 90,
        'usd_price': 0.49,
        'rarity': 'common',
        'category': 'consumable',
        'image_url': f'{IMG}/tango.png',
    },
    {
        'name': 'Dust of Appearance',
        'description': "Reveals invisible heroes in a 1050 radius. Slows by 20%.",
        'gold_cost': 80,
        'usd_price': 1.49,
        'rarity': 'common',
        'category': 'consumable',
        'image_url': f'{IMG}/dust.png',
    },
    {
        'name': 'Smoke of Deceit',
        'description': "Grants invisibility to you and nearby allied heroes for 35 seconds.",
        'gold_cost': 50,
        'usd_price': 1.99,
        'rarity': 'uncommon',
        'category': 'consumable',
        'image_url': f'{IMG}/smoke_of_deceit.png',
    },
    # ---- Hero Skins ----
    {
        'name': 'Juggernaut - Dragon Knight Set',
        'description': "Legendary armor set for Juggernaut. Dragon-themed blade and mask with golden accents.",
        'gold_cost': 0,
        'usd_price': 14.99,
        'rarity': 'legendary',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_juggernaut.png',
    },
    {
        'name': 'Phantom Assassin - Manifold Paradox',
        'description': "Arcana weapon for Phantom Assassin. Ethereal blades that shimmer between dimensions.",
        'gold_cost': 0,
        'usd_price': 34.99,
        'rarity': 'legendary',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_phantom_assassin.png',
    },
    {
        'name': 'Invoker - Dark Artistry',
        'description': "Full set for Invoker. Cape, orbs, and hair restyled with dark magical energy.",
        'gold_cost': 0,
        'usd_price': 29.99,
        'rarity': 'legendary',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_invoker.png',
    },
    {
        'name': 'Crystal Maiden - Frost Avalanche',
        'description': "Arcana for Crystal Maiden. Frostwyrm companion and icy aura effects.",
        'gold_cost': 0,
        'usd_price': 34.99,
        'rarity': 'legendary',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_crystal_maiden.png',
    },
    {
        'name': 'Anti-Mage - Guilt of the Survivor',
        'description': "Persona for Anti-Mage. Female warrior variant with twin blades of vengeance.",
        'gold_cost': 0,
        'usd_price': 24.99,
        'rarity': 'rare',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_antimage.png',
    },
    {
        'name': 'Pudge - Dapper Disguise',
        'description': "Legendary set for Pudge. Top hat, monocle, and a very sharp hook.",
        'gold_cost': 0,
        'usd_price': 12.99,
        'rarity': 'rare',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_pudge.png',
    },
    {
        'name': 'Axe - Red Mist Reaper',
        'description': "Immortal set for Axe. Burning red axe blade with fiery particle effects.",
        'gold_cost': 0,
        'usd_price': 19.99,
        'rarity': 'legendary',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_axe.png',
    },
    {
        'name': 'Drow Ranger - Monarch Bow',
        'description': "Rare set for Drow Ranger. Elegant ice bow with crystalline arrows.",
        'gold_cost': 0,
        'usd_price': 9.99,
        'rarity': 'rare',
        'category': 'hero_skin',
        'image_url': f'{IMG}/hero_drow_ranger.png',
    },
]


class Command(BaseCommand):
    help = 'Seed Dota 2 items into the database'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing items before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            count = Dota2Item.objects.count()
            Dota2Item.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing items'))

        created = 0
        updated = 0
        for data in ITEMS:
            item, created_flag = Dota2Item.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created_flag:
                created += 1
                self.stdout.write(f'  Created: {item.name}')
            else:
                changed = False
                for key, value in data.items():
                    if getattr(item, key) != value:
                        setattr(item, key, value)
                        changed = True
                if changed:
                    item.save()
                    updated += 1
                    self.stdout.write(f'  Updated: {item.name}')

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {created} new, updated {updated} existing (total: {Dota2Item.objects.count()})'
        ))
