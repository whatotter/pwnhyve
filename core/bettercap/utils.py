"""
ALL of this script will be from pwnagotchi's utils module
"""

class WifiInfo:
    """
    Fields you can extract from a pcap file
    """
    BSSID = 0
    ESSID = 1
    ENCRYPTION = 2
    CHANNEL = 3
    RSSI = 4

def extract_from_pcap(path, fields):
    """
    Search in pcap-file for specified information
    path: Path to pcap file
    fields: Array of fields that should be extracted
    If a field is not found, KeyError is raised
    """
    results = dict()
    for field in fields:
        if not isinstance(field, WifiInfo):
            raise TypeError("Invalid field")

        subtypes = set()

        if field == WifiInfo.BSSID:
            from scapy.all import Dot11Beacon, Dot11ProbeResp, Dot11AssoReq, Dot11ReassoReq, Dot11, sniff
            subtypes.add('beacon')
            bpf_filter = " or ".join([f"wlan type mgt subtype {subtype}" for subtype in subtypes])
            packets = sniff(offline=path, filter=bpf_filter)
            try:
                for packet in packets:
                    if packet.haslayer(Dot11Beacon):
                        if hasattr(packet[Dot11], 'addr3'):
                            results[field] = packet[Dot11].addr3
                            break
                else:  # magic
                    raise KeyError("Could not find field [BSSID]")
            except Exception:
                raise KeyError("Could not find field [BSSID]")
        elif field == WifiInfo.ESSID:
            from scapy.all import Dot11Beacon, Dot11ReassoReq, Dot11AssoReq, Dot11, sniff, Dot11Elt
            subtypes.add('beacon')
            subtypes.add('assoc-req')
            subtypes.add('reassoc-req')
            bpf_filter = " or ".join([f"wlan type mgt subtype {subtype}" for subtype in subtypes])
            packets = sniff(offline=path, filter=bpf_filter)
            try:
                for packet in packets:
                    if packet.haslayer(Dot11Elt) and hasattr(packet[Dot11Elt], 'info'):
                        results[field] = packet[Dot11Elt].info.decode('utf-8')
                        break
                else:  # magic
                    raise KeyError("Could not find field [ESSID]")
            except Exception:
                raise KeyError("Could not find field [ESSID]")
        elif field == WifiInfo.ENCRYPTION:
            from scapy.all import Dot11Beacon, sniff
            subtypes.add('beacon')
            bpf_filter = " or ".join([f"wlan type mgt subtype {subtype}" for subtype in subtypes])
            packets = sniff(offline=path, filter=bpf_filter)
            try:
                for packet in packets:
                    if packet.haslayer(Dot11Beacon) and hasattr(packet[Dot11Beacon], 'network_stats'):
                        stats = packet[Dot11Beacon].network_stats()
                        if 'crypto' in stats:
                            results[field] = stats['crypto']  # set with encryption types
                            break
                else:  # magic
                    raise KeyError("Could not find field [ENCRYPTION]")
            except Exception:
                raise KeyError("Could not find field [ENCRYPTION]")
        elif field == WifiInfo.CHANNEL:
            from scapy.all import sniff, RadioTap
            from core.bettercap.bettercap import freq_to_channel
            packets = sniff(offline=path, count=1)
            try:
                results[field] = freq_to_channel(packets[0][RadioTap].ChannelFrequency)
            except Exception:
                raise KeyError("Could not find field [CHANNEL]")
        elif field == WifiInfo.RSSI:
            from scapy.all import sniff, RadioTap
            from core.bettercap.bettercap import freq_to_channel
            packets = sniff(offline=path, count=1)
            try:
                results[field] = packets[0][RadioTap].dBm_AntSignal
            except Exception:
                raise KeyError("Could not find field [RSSI]")

    return results