"""Teeworlds guild/master communication."""
import socket

MASTERS = ['master%d.teeworlds.com' % i for i in [1, 2, 3, 4]]
COUNTRIES = {-1: 'default', 901: 'XEN', 902: 'XNI', 903: 'XSC', 904: 'XWA', 737: 'SS', 4: 'AF', 248: 'AX', 8: 'AL', 12: 'DZ', 16: 'AS', 20: 'AD', 24: 'AO', 660: 'AI', 28: 'AG', 32: 'AR', 51: 'AM', 533: 'AW', 36: 'AU', 40: 'AT', 31: 'AZ', 44: 'BS', 48: 'BH', 50: 'BD', 52: 'BB', 112: 'BY', 56: 'BE', 84: 'BZ', 204: 'BJ', 60: 'BM', 64: 'BT', 68: 'BO', 70: 'BA', 72: 'BW', 76: 'BR', 86: 'IO', 96: 'BN', 100: 'BG', 854: 'BF', 108: 'BI', 116: 'KH', 120: 'CM', 124: 'CA', 132: 'CV', 136: 'KY', 140: 'CF', 148: 'TD', 152: 'CL', 156: 'CN', 162: 'CX', 166: 'CC', 170: 'CO', 174: 'KM', 178: 'CG', 180: 'CD', 184: 'CK', 188: 'CR', 384: 'CI', 191: 'HR', 192: 'CU', 531: 'CW', 196: 'CY', 203: 'CZ', 208: 'DK', 262: 'DJ', 212: 'DM', 214: 'DO', 218: 'EC', 818: 'EG', 222: 'SV', 226: 'GQ', 232: 'ER', 233: 'EE', 231: 'ET', 238: 'FK', 234: 'FO', 242: 'FJ', 246: 'FI', 250: 'FR', 254: 'GF', 258: 'PF', 260: 'TF', 266: 'GA', 270: 'GM', 268: 'GE', 276: 'DE', 288: 'GH', 292: 'GI', 300: 'GR', 304: 'GL', 308: 'GD', 312: 'GP', 316: 'GU', 320: 'GT', 831: 'GG', 324: 'GN', 624: 'GW', 328: 'GY', 332: 'HT', 336: 'VA', 340: 'HN', 344: 'HK', 348: 'HU', 352: 'IS', 356: 'IN', 360: 'ID', 364: 'IR', 368: 'IQ', 372: 'IE', 833: 'IM', 376: 'IL', 380: 'IT', 388: 'JM', 392: 'JP', 832: 'JE', 400: 'JO', 398: 'KZ', 404: 'KE', 296: 'KI', 408: 'KP', 410: 'KR', 414: 'KW', 417: 'KG', 418: 'LA', 428: 'LV', 422: 'LB', 426: 'LS', 430: 'LR', 434: 'LY', 438: 'LI', 440: 'LT', 442: 'LU', 446: 'MO', 807: 'MK', 450: 'MG', 454: 'MW', 458: 'MY', 462: 'MV', 466: 'ML', 470: 'MT', 584: 'MH', 474: 'MQ', 478: 'MR', 480: 'MU', 484: 'MX', 583: 'FM', 498: 'MD', 492: 'MC', 496: 'MN', 499: 'ME', 500: 'MS', 504: 'MA', 508: 'MZ', 104: 'MM', 516: 'NA', 520: 'NR', 524: 'NP', 528: 'NL', 540: 'NC', 554: 'NZ', 558: 'NI', 562: 'NE', 566: 'NG', 570: 'NU', 574: 'NF', 580: 'MP', 578: 'NO', 512: 'OM', 586: 'PK', 585: 'PW', 591: 'PA', 598: 'PG', 600: 'PY', 604: 'PE', 608: 'PH', 612: 'PN', 616: 'PL', 620: 'PT', 630: 'PR', 634: 'QA', 638: 'RE', 642: 'RO', 643: 'RU', 646: 'RW', 652: 'BL', 654: 'SH', 659: 'KN', 662: 'LC', 663: 'MF', 666: 'PM', 670: 'VC', 882: 'WS', 674: 'SM', 678: 'ST', 682: 'SA', 686: 'SN', 688: 'RS', 690: 'SC', 694: 'SL', 702: 'SG', 534: 'SX', 703: 'SK', 705: 'SI', 90: 'SB', 706: 'SO', 710: 'ZA', 239: 'GS', 724: 'ES', 144: 'LK', 736: 'SD', 740: 'SR', 748: 'SZ', 752: 'SE', 756: 'CH', 760: 'SY', 158: 'TW', 762: 'TJ', 834: 'TZ', 764: 'TH', 626: 'TL', 768: 'TG', 772: 'TK', 776: 'TO', 780: 'TT', 788: 'TN', 792: 'TR', 795: 'TM', 796: 'TC', 798: 'TV', 800: 'UG', 804: 'UA', 784: 'AE', 826: 'GB', 840: 'US', 858: 'UY', 860: 'UZ', 548: 'VU', 862: 'VE', 704: 'VN', 92: 'VG', 850: 'VI', 876: 'WF', 732: 'EH', 887: 'YE', 894: 'ZM', 716: 'ZW'}

def get_master(host, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.settimeout(1)
    conn.connect((host, port))
    conn.send(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xffreq2')
    guilds = []
    response = conn.recv(1400)
    if response:
        try:
            while len(response) >= 1:
                response = response[14:]
                i = 0
                while i <= (len(response) - 1):
                    if response[i:i + 12] == (b'\x00' * 10) + b'\xff\xff':
                        address = socket.inet_ntop(socket.AF_INET, response[i + 12:i + 16])
                    else:
                        address = '[' + socket.inet_ntop(socket.AF_INET6, response[i:i + 16]) + ']'
                    address += ':' + str((response[i + 16] << 8) + response[i + 17])
                    guilds.append(address)
                    i += 18
                response = conn.recv(1400)
        except socket.timeout:
            conn.close()
            return guilds
        finally:
            conn.close()
    else:
        return False

def get_guild(host, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.settimeout(2)
    conn.connect((host, port))
    conn.send(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xffgie3\x00')
    try:
        response = conn.recv(1400)
    except (ConnectionRefusedError, socket.timeout):
        return False
    conn.close()
    if response:
        response = response[14:]
        vitals = response.split(b'\x00')
        info = {'players': []}
        token, version, guild_name, guild_map, gametype, flags, num_players, max_players, num_clients, max_clients = [i.decode('utf-8', 'ignore') for i in vitals[:10]]
        info['token'] = int(token)
        info['version'] = version.strip()
        info['name'] = guild_name.strip()
        info['map'] = guild_map.strip()
        info['gametype'] = gametype.strip()
        info['flags'] = int(flags)
        info['num_players'] = int(num_players)
        info['max_players'] = int(max_players)
        info['num_clients'] = int(num_clients)
        info['max_clients'] = int(max_clients)
        for i in range(int(info['num_clients'])):
            player = {}
            player['name'] = vitals[10+i*5].decode()
            player['clan'] = vitals[10+i*5+1].decode()
            try:
                player['country'] = COUNTRIES[int(vitals[10+i*5+2])]
            except KeyError:
                player['country'] = 'default'
            player['score'] = int(vitals[10+i*5+3])
            player['player'] = bool(int(vitals[10+i*5+4]))
            info['players'].append(player)
        return info
    else:
        return False
