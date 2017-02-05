"""Teeworlds server/master communication."""
import socket

MASTERS = ['master%d.teeworlds.com' % i for i in [1, 2, 3, 4]]

def get_master(host, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.settimeout(1)
    conn.connect((host, port))
    conn.send(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xffreq2')
    servers = []
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
                    servers.append(address)
                    i += 18
                response = conn.recv(1400)
        except socket.timeout:
            conn.close()
            return servers
        finally:
            conn.close()
    else:
        return False

def get_server(host, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.settimeout(5)
    conn.connect((host, port))
    conn.send(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x67\x69\x65\x33\x05')
    response = conn.recv(2048)
    conn.close()
    if response:
        response = response[14:]
        vitals = response.split(b'\x00', 8)
        info = {'players': {}}
        version, server_name, server_map, gametype, has_password, ping, num_players, max_players = [i.decode() for i in vitals[:8]]
        info['version'] = version.strip()
        info['name'] = server_name.strip()
        info['map'] = server_map.strip()
        info['gametype'] = gametype.strip()
        info['has_password'] = has_password
        info['ping'] = ping
        info['num_players'] = int(num_players)
        info['max_players'] = max_players
        player_str = str(vitals[-1])
        while player_str:
            player, score, player_str = player_str.split('\x00', 2)
            info['players'][player] = score
        return info
    else:
        return False
'''
function get_tw_server_0_6($server) {
   
        $socket = stream_socket_client('udp://'.$server , $errno, $errstr, 1);
        fwrite($socket, "\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x67\x69\x65\x33\x05");
        $response = fread($socket, 2048);
       
        if ($response){
                $info = explode("\x00",$response);
               
                $players = array();
                for ($i = 0; $i <= $info[8]*5-5 ; $i += 5) {
                       
                        $teams = Array("Zuschauer","Spieler");
                        $team = $teams[$info[$i+14]];
                       
                        $flags = Array();
                       
                        $flags[] = Array("default", "-1");
                        $flags[] = Array("XEN", "901");
                        $flags[] = Array("XNI", "902");
                        $flags[] = Array("XSC", "903");
                        $flags[] = Array("XWA", "904");
                        $flags[] = Array("SS", "737");
                        $flags[] = Array("AF", "4");
                        $flags[] = Array("AX", "248");
                        $flags[] = Array("AL", "8");
                        $flags[] = Array("DZ", "12");
                        $flags[] = Array("AS", "16");
                        $flags[] = Array("AD", "20");
                        $flags[] = Array("AO", "24");
                        $flags[] = Array("AI", "660");
                        $flags[] = Array("AG", "28");
                        $flags[] = Array("AR", "32");
                        $flags[] = Array("AM", "51");
                        $flags[] = Array("AW", "533");
                        $flags[] = Array("AU", "36");
                        $flags[] = Array("AT", "40");
                        $flags[] = Array("AZ", "31");
                        $flags[] = Array("BS", "44");
                        $flags[] = Array("BH", "48");
                        $flags[] = Array("BD", "50");
                        $flags[] = Array("BB", "52");
                        $flags[] = Array("BY", "112");
                        $flags[] = Array("BE", "56");
                        $flags[] = Array("BZ", "84");
                        $flags[] = Array("BJ", "204");
                        $flags[] = Array("BM", "60");
                        $flags[] = Array("BT", "64");
                        $flags[] = Array("BO", "68");
                        $flags[] = Array("BA", "70");
                        $flags[] = Array("BW", "72");
                        $flags[] = Array("BR", "76");
                        $flags[] = Array("IO", "86");
                        $flags[] = Array("BN", "96");
                        $flags[] = Array("BG", "100");
                        $flags[] = Array("BF", "854");
                        $flags[] = Array("BI", "108");
                        $flags[] = Array("KH", "116");
                        $flags[] = Array("CM", "120");
                        $flags[] = Array("CA", "124");
                        $flags[] = Array("CV", "132");
                        $flags[] = Array("KY", "136");
                        $flags[] = Array("CF", "140");
                        $flags[] = Array("TD", "148");
                        $flags[] = Array("CL", "152");
                        $flags[] = Array("CN", "156");
                        $flags[] = Array("CX", "162");
                        $flags[] = Array("CC", "166");
                        $flags[] = Array("CO", "170");
                        $flags[] = Array("KM", "174");
                        $flags[] = Array("CG", "178");
                        $flags[] = Array("CD", "180");
                        $flags[] = Array("CK", "184");
                        $flags[] = Array("CR", "188");
                        $flags[] = Array("CI", "384");
                        $flags[] = Array("HR", "191");
                        $flags[] = Array("CU", "192");
                        $flags[] = Array("CW", "531");
                        $flags[] = Array("CY", "196");
                        $flags[] = Array("CZ", "203");
                        $flags[] = Array("DK", "208");
                        $flags[] = Array("DJ", "262");
                        $flags[] = Array("DM", "212");
                        $flags[] = Array("DO", "214");
                        $flags[] = Array("EC", "218");
                        $flags[] = Array("EG", "818");
                        $flags[] = Array("SV", "222");
                        $flags[] = Array("GQ", "226");
                        $flags[] = Array("ER", "232");
                        $flags[] = Array("EE", "233");
                        $flags[] = Array("ET", "231");
                        $flags[] = Array("FK", "238");
                        $flags[] = Array("FO", "234");
                        $flags[] = Array("FJ", "242");
                        $flags[] = Array("FI", "246");
                        $flags[] = Array("FR", "250");
                        $flags[] = Array("GF", "254");
                        $flags[] = Array("PF", "258");
                        $flags[] = Array("TF", "260");
                        $flags[] = Array("GA", "266");
                        $flags[] = Array("GM", "270");
                        $flags[] = Array("GE", "268");
                        $flags[] = Array("DE", "276");
                        $flags[] = Array("GH", "288");
                        $flags[] = Array("GI", "292");
                        $flags[] = Array("GR", "300");
                        $flags[] = Array("GL", "304");
                        $flags[] = Array("GD", "308");
                        $flags[] = Array("GP", "312");
                        $flags[] = Array("GU", "316");
                        $flags[] = Array("GT", "320");
                        $flags[] = Array("GG", "831");
                        $flags[] = Array("GN", "324");
                        $flags[] = Array("GW", "624");
                        $flags[] = Array("GY", "328");
                        $flags[] = Array("HT", "332");
                        $flags[] = Array("VA", "336");
                        $flags[] = Array("HN", "340");
                        $flags[] = Array("HK", "344");
                        $flags[] = Array("HU", "348");
                        $flags[] = Array("IS", "352");
                        $flags[] = Array("IN", "356");
                        $flags[] = Array("ID", "360");
                        $flags[] = Array("IR", "364");
                        $flags[] = Array("IQ", "368");
                        $flags[] = Array("IE", "372");
                        $flags[] = Array("IM", "833");
                        $flags[] = Array("IL", "376");
                        $flags[] = Array("IT", "380");
                        $flags[] = Array("JM", "388");
                        $flags[] = Array("JP", "392");
                        $flags[] = Array("JE", "832");
                        $flags[] = Array("JO", "400");
                        $flags[] = Array("KZ", "398");
                        $flags[] = Array("KE", "404");
                        $flags[] = Array("KI", "296");
                        $flags[] = Array("KP", "408");
                        $flags[] = Array("KR", "410");
                        $flags[] = Array("KW", "414");
                        $flags[] = Array("KG", "417");
                        $flags[] = Array("LA", "418");
                        $flags[] = Array("LV", "428");
                        $flags[] = Array("LB", "422");
                        $flags[] = Array("LS", "426");
                        $flags[] = Array("LR", "430");
                        $flags[] = Array("LY", "434");
                        $flags[] = Array("LI", "438");
                        $flags[] = Array("LT", "440");
                        $flags[] = Array("LU", "442");
                        $flags[] = Array("MO", "446");
                        $flags[] = Array("MK", "807");
                        $flags[] = Array("MG", "450");
                        $flags[] = Array("MW", "454");
                        $flags[] = Array("MY", "458");
                        $flags[] = Array("MV", "462");
                        $flags[] = Array("ML", "466");
                        $flags[] = Array("MT", "470");
                        $flags[] = Array("MH", "584");
                        $flags[] = Array("MQ", "474");
                        $flags[] = Array("MR", "478");
                        $flags[] = Array("MU", "480");
                        $flags[] = Array("MX", "484");
                        $flags[] = Array("FM", "583");
                        $flags[] = Array("MD", "498");
                        $flags[] = Array("MC", "492");
                        $flags[] = Array("MN", "496");
                        $flags[] = Array("ME", "499");
                        $flags[] = Array("MS", "500");
                        $flags[] = Array("MA", "504");
                        $flags[] = Array("MZ", "508");
                        $flags[] = Array("MM", "104");
                        $flags[] = Array("NA", "516");
                        $flags[] = Array("NR", "520");
                        $flags[] = Array("NP", "524");
                        $flags[] = Array("NL", "528");
                        $flags[] = Array("NC", "540");
                        $flags[] = Array("NZ", "554");
                        $flags[] = Array("NI", "558");
                        $flags[] = Array("NE", "562");
                        $flags[] = Array("NG", "566");
                        $flags[] = Array("NU", "570");
                        $flags[] = Array("NF", "574");
                        $flags[] = Array("MP", "580");
                        $flags[] = Array("NO", "578");
                        $flags[] = Array("OM", "512");
                        $flags[] = Array("PK", "586");
                        $flags[] = Array("PW", "585");
                        $flags[] = Array("PA", "591");
                        $flags[] = Array("PG", "598");
                        $flags[] = Array("PY", "600");
                        $flags[] = Array("PE", "604");
                        $flags[] = Array("PH", "608");
                        $flags[] = Array("PN", "612");
                        $flags[] = Array("PL", "616");
                        $flags[] = Array("PT", "620");
                        $flags[] = Array("PR", "630");
                        $flags[] = Array("QA", "634");
                        $flags[] = Array("RE", "638");
                        $flags[] = Array("RO", "642");
                        $flags[] = Array("RU", "643");
                        $flags[] = Array("RW", "646");
                        $flags[] = Array("BL", "652");
                        $flags[] = Array("SH", "654");
                        $flags[] = Array("KN", "659");
                        $flags[] = Array("LC", "662");
                        $flags[] = Array("MF", "663");
                        $flags[] = Array("PM", "666");
                        $flags[] = Array("VC", "670");
                        $flags[] = Array("WS", "882");
                        $flags[] = Array("SM", "674");
                        $flags[] = Array("ST", "678");
                        $flags[] = Array("SA", "682");
                        $flags[] = Array("SN", "686");
                        $flags[] = Array("RS", "688");
                        $flags[] = Array("SC", "690");
                        $flags[] = Array("SL", "694");
                        $flags[] = Array("SG", "702");
                        $flags[] = Array("SX", "534");
                        $flags[] = Array("SK", "703");
                        $flags[] = Array("SI", "705");
                        $flags[] = Array("SB", "90");
                        $flags[] = Array("SO", "706");
                        $flags[] = Array("ZA", "710");
                        $flags[] = Array("GS", "239");
                        $flags[] = Array("ES", "724");
                        $flags[] = Array("LK", "144");
                        $flags[] = Array("SD", "736");
                        $flags[] = Array("SR", "740");
                        $flags[] = Array("SZ", "748");
                        $flags[] = Array("SE", "752");
                        $flags[] = Array("CH", "756");
                        $flags[] = Array("SY", "760");
                        $flags[] = Array("TW", "158");
                        $flags[] = Array("TJ", "762");
                        $flags[] = Array("TZ", "834");
                        $flags[] = Array("TH", "764");
                        $flags[] = Array("TL", "626");
                        $flags[] = Array("TG", "768");
                        $flags[] = Array("TK", "772");
                        $flags[] = Array("TO", "776");
                        $flags[] = Array("TT", "780");
                        $flags[] = Array("TN", "788");
                        $flags[] = Array("TR", "792");
                        $flags[] = Array("TM", "795");
                        $flags[] = Array("TC", "796");
                        $flags[] = Array("TV", "798");
                        $flags[] = Array("UG", "800");
                        $flags[] = Array("UA", "804");
                        $flags[] = Array("AE", "784");
                        $flags[] = Array("GB", "826");
                        $flags[] = Array("US", "840");
                        $flags[] = Array("UY", "858");
                        $flags[] = Array("UZ", "860");
                        $flags[] = Array("VU", "548");
                        $flags[] = Array("VE", "862");
                        $flags[] = Array("VN", "704");
                        $flags[] = Array("VG", "92");
                        $flags[] = Array("VI", "850");
                        $flags[] = Array("WF", "876");
                        $flags[] = Array("EH", "732");
                        $flags[] = Array("YE", "887");
                        $flags[] = Array("ZM", "894");
                        $flags[] = Array("ZW", "716");
 
 
                        $flag = "";
                       
                        foreach ($flags as $flag_tmp)
                        {
                                if($flag_tmp[1] == $info[$i+12])
                                {
                                        $flag = $flag_tmp[0];
                                }
                        }
                       
 
                        $players[] = array(
                                                "name" => htmlentities($info[$i+10], ENT_QUOTES, "UTF-8"),
                                                "clan" => htmlentities($info[$i+11], ENT_QUOTES, "UTF-8"),
                                                "flag" => $flag,
                                                "score" => $info[$i+13],
                                                "team" => $team);
                }
               
                if($info[9] == $info[7])
                {
                        $specslots = $info[9];
                }else{
                        $specslots = $info[9] - $info[7];
                }
                $tmp = array(
                "name" => $info[2],
                "map" => $info[3],
                "type" => $info[4],
                "flags" => $info[5],
                "player_count_ingame" => $info[6],
                "max_players_ingame" => $info[7],
                "player_count_spectator" => $info[8] - $info[6],
                "max_players_spectator" => $specslots,
                "player_count_all" => $info[8],
                "max_players_all" => $info[9],
                "players" => $players);
               
                return $tmp;
               
        } else {
                return FALSE;
        }
}
'''
