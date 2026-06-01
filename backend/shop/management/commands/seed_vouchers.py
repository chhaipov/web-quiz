"""
Management command to seed sample vouchers
"""
from django.core.management.base import BaseCommand
from shop.models import Voucher, Dota2Item


class Command(BaseCommand):
    help = 'Seed sample vouchers into the database'

    def handle(self, *args, **options):
        created = 0

        wallet_vouchers = [
            {'code': 'WELCOME50', 'type': 'wallet', 'wallet_amount': 50.00, 'max_claims': 100},
            {'code': 'BONUS25', 'type': 'wallet', 'wallet_amount': 25.00, 'max_claims': 50},
            {'code': 'VIP100', 'type': 'wallet', 'wallet_amount': 100.00, 'max_claims': 10},
            {'code': 'FREEBIE10', 'type': 'wallet', 'wallet_amount': 10.00, 'max_claims': 200},
            {'code': 'JACKPOT500', 'type': 'wallet', 'wallet_amount': 500.00, 'max_claims': 1},
        ]

        for data in wallet_vouchers:
            _, c = Voucher.objects.get_or_create(code=data['code'], defaults=data)
            if c:
                created += 1
                self.stdout.write(f'  Created wallet voucher: {data["code"]} (${data["wallet_amount"]})')

        skin_names = [
            'Juggernaut - Dragon Knight Set',
            'Phantom Assassin - Manifold Paradox',
            'Invoker - Dark Artistry',
            'Crystal Maiden - Frost Avalanche',
        ]

        for name in skin_names:
            item = Dota2Item.objects.filter(name=name).first()
            if not item:
                continue
            code = f'FREE-{name.split(" - ")[0].upper().replace(" ", "")}'
            _, c = Voucher.objects.get_or_create(
                code=code,
                defaults={
                    'type': 'item',
                    'item': item,
                    'item_quantity': 1,
                    'max_claims': 5,
                }
            )
            if c:
                created += 1
                self.stdout.write(f'  Created item voucher: {code} -> {item.name}')

        item_names = [
            ('FREEBLINK', 'Blink Dagger', 1, 20),
            ('FREERAPIER', 'Divine Rapier', 1, 3),
        ]
        for code, iname, qty, max_c in item_names:
            item = Dota2Item.objects.filter(name=iname).first()
            if not item:
                continue
            _, c = Voucher.objects.get_or_create(
                code=code,
                defaults={
                    'type': 'item',
                    'item': item,
                    'item_quantity': qty,
                    'max_claims': max_c,
                }
            )
            if c:
                created += 1
                self.stdout.write(f'  Created item voucher: {code} -> {qty}x {item.name}')

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {created} new vouchers (total: {Voucher.objects.count()})'
        ))
