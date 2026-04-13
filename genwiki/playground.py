"""
Created on 2024-10-24

@author: wf
"""

import argparse
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class God:
    """
    A Greek god entry with name and image references.
    """

    name: str
    local_img: str
    img: str


# Color definitions
BLUE = "\033[0;34m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
ENDC = "\033[0m"


class Playground:
    """
    a class to create wiki playgrounds
    """

    def __init__(
        self,
        base_port: int = 9100,
        host: str = "wiki-playground.genealogy.net",
        apache_port: int = 8080,
    ):
        self.base_port = base_port
        self.step = 2  # Port step (for mw_port and sql_port)
        self.host = host
        self.apache_port = apache_port

    def color_msg(self, color: str, msg: str) -> None:
        """Displays colored messages."""
        print(f"{color}{msg}{ENDC}")

    def godsList(self) -> List[God]:
        """
        Returns the list of Greek gods with their name, local image filename,
        and Wikimedia Commons source URL.
        """
        return [
            God(
                "Aglaea",
                "Aglaea.JPG",
                "http://commons.wikimedia.org/wiki/Special:FilePath/20140416%20corfu218.JPG",
            ),
            God(
                "Amicitia",
                "Amicitia.JPG",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Amicitia%20DenHaag%20Friedenspalast.JPG",
            ),
            God(
                "Anteros",
                "Anteros.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Eros-piccadilly-circus.jpg",
            ),
            God(
                "Ares",
                "Ares.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/%CE%9F%20%CE%86%CF%81%CE%B7%CF%82%20%28Borghese-%CE%9B%CE%BF%CF%8D%CE%B2%CF%81%CE%BF%CF%85%29.jpg",
            ),
            God(
                "Aristaeus",
                "Aristaeus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Aristaeus%20Bosio%20Louvre%20LL51.jpg",
            ),
            God(
                "Artemis",
                "Artemis.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/The%20Artemis%20of%20Ephesus.jpg",
            ),
            God(
                "Bia",
                "Bia.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Henry%20Fuseli%20-%20Hephaestus%2C%20Bia%20and%20Crato%20Securing%20Prometheus%20on%20Mount%20Caucasus%20-%20Google%20Art%20Project.jpg",
            ),
            God(
                "Britomartis",
                "Britomartis.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Email%20Limoges%20Spiegelr%C3%BCckseite%20Minos%20und%20Britomaris%20makffm%20WMH8.jpg",
            ),
            God(
                "Carpo",
                "Carpo.JPG",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Carpo-hora%2C%20I%20secolo%20dc%2C%20%28Uffizi%29%2003.JPG",
            ),
            God(
                "Charon",
                "Charon.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Sabouroff%20Painter%20ARV%20846%20196%20Hermes%20leading%20a%20deceased%20to%20Charon%20%2802%29.jpg",
            ),
            God(
                "Deimos",
                "Deimos.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Deimos-e-phoboslllll.jpg",
            ),
            God(
                "Demeter",
                "Demeter.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/%28Venice%29%20Demeter%20in%20the%20Museo%20archeologico%20nazionale.jpg",
            ),
            God(
                "Despoina",
                "Despoina.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Lycosoura-group%20%28cropped%29.jpg",
            ),
            God(
                "Eileithyia",
                "Eileithyia.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Amphora%20birth%20Athena%20Louvre%20F32.jpg",
            ),
            God(
                "Eirene",
                "Eirene.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Eirene%20von%20Knaus.jpg",
            ),
            God(
                "Enyo",
                "Enyo.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Image%20of%20Enyo%20the%20Goddess-%202014-04-16%2007-17.jpg",
            ),
            God(
                "Eos",
                "Eos.png",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Eos%20utgjutande%20morgondaggen%2C%20Nordisk%20familjebok.png",
            ),
            God(
                "Eris",
                "Eris.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Eris%20Antikensammlung%20Berlin%20F1775.jpg",
            ),
            God(
                "Eunomia",
                "Eunomia.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Horen%20Meyers.jpg",
            ),
            God(
                "Euphrosyne",
                "Euphrosyne.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Euphrosyne%20statue%20-%20Achilleion.jpg",
            ),
            God(
                "Hades",
                "Hades.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Detail%20of%20Pluto-Serapis%2C%20Statue%20group%20of%20Persephone%20%28as%20Isis%29%20and%20Pluto%20%28as%20Serapis%29%2C%20from%20the%20Sanctuary%20of%20the%20Egyptian%20Gods%20at%20Gortyna%2C%20mid-2nd%20century%20AD%2C%20Heraklion%20Archaeological%20Museum%20%2830305313721%29.jpg",
            ),
            God(
                "Hebe",
                "Hebe.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Canova-Hebe%2030%20degree%20view.jpg",
            ),
            God(
                "Helios",
                "Helios.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Architrave%20with%20sculpted%20metope%20showing%20sun%20god%20Helios%20in%20a%20quadriga%3B%20from%20temple%20of%20Athena%20at%20Troy%2C%20ca%20300-280%20BCE%3B%20Altes%20Museum%2C%20Berlin%20%2825308440197%29%20%28cropped%29%201.jpg",
            ),
            God(
                "Hemera",
                "Hemera.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Aphrodisias%20Museum%20Hemera%20or%20Day%204627.jpg",
            ),
            God(
                "Hephaestus",
                "Hephaestus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Hephaistos%20Thetis%20at%20Kylix%20by%20the%20Foundry%20Painter%20Antikensammlung%20Berlin%20F2294.jpg",
            ),
            God(
                "Hera",
                "Hera.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Hera%20Campana%20Louvre%20Ma2283.jpg",
            ),
            God(
                "Hermaphroditus",
                "Hermaphroditus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Ermafrodito%20-%20sec.%20III%20a.C.%20-%20da%20Pergamo.%20Istanbul.%20Museo%20archeol..jpg",
            ),
            God(
                "Hestia",
                "Hestia.JPG",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Hestia%20-%20Wellesley%20College%20-%20DSC09634.JPG",
            ),
            God(
                "Himeros",
                "Himeros.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Kantharos64.10.jpg",
            ),
            God(
                "Hypnos",
                "Hypnos.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Waterhouse-sleep%20and%20his%20half-brother%20death-1874.jpg",
            ),
            God(
                "Iris",
                "Iris.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Iris%20Louvre%20L43%20n2.jpg",
            ),
            God(
                "Kratos",
                "Kratos.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Kratos%20by%20John%20Flaxman.jpg",
            ),
            God(
                "Momus",
                "Momus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Nantes%20-%20Graslin%20int%2001.jpg",
            ),
            God(
                "Nike",
                "Nike.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Nik%C3%A9%20%C3%89ph%C3%A8se.jpg",
            ),
            God(
                "Panacea",
                "Panacea.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Panacea.jpg",
            ),
            God(
                "Phobos",
                "Phobos.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Gigantomachy%20Staatliche%20Antikensammlungen%201553.jpg",
            ),
            God(
                "Phosphorus",
                "Phosphorus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Evelyn%20de%20Morgan%20-%20Phosphorus%20and%20Hesperus%2C%20%281881%29.jpg",
            ),
            God(
                "Plutus",
                "Plutus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Eirene%20Ploutos%20Glyptothek%20Munich%20219%20n4.jpg",
            ),
            God(
                "Poseidon",
                "Poseidon.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Poseidon%20sculpture%20Copenhagen%202005.jpg",
            ),
            God(
                "Telesphorus",
                "Telesphorus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Statue%20of%20Telesphorus%2C%20Greece%2C%20500-200%20BCE%20Wellcome%20L0058862.jpg",
            ),
            God(
                "Thalia",
                "Thalia.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Thalia%20at%20Corfu%201.jpg",
            ),
            God(
                "Thallo",
                "Thallo.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/The%20Spring%20by%20Franz%20Xaver%20Winterhalter.jpg",
            ),
            God(
                "Thanatos",
                "Thanatos.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Euphronios%20krater%20side%20A%20MET%20L.2006.10.jpg",
            ),
            God(
                "Zeus",
                "Zeus.jpg",
                "http://commons.wikimedia.org/wiki/Special:FilePath/Jupiter%20J1a.jpg",
            ),
        ]

    def generate_header(self, image_url: str) -> str:
        """
        Generates the HTML header section with the logo on the left and the title aligned to the right on the same line.
        """
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>CompGen - Semantic MediaWiki Spielwiesen</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 0; margin: 0; }}
        .header {{
            background-color: #2d4899;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .header img {{ width: 100px; }}
        .header h1 {{ color: white; font-size: 24px; margin: 0; }}
        .container {{  margin: 20px auto; padding: 10px; }}
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(9, 1fr);
            gap: 10px;
        }}
        .grid-item {{ text-align: center; }}
        /*
\t   We need to show 44 images in a 5 rows by 9 column grid
\t   */
\t.grid-item img {{ width: 105px; height: 105px; object-fit: cover; }}
        a {{ color: #2d4899; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <img src="{image_url}" alt="CompGen Logo">
        <h1>Semantic MediaWiki Spielwiesen</h1>
    </div>
    <div class="container">
"""

    def generate_table(self) -> str:
        """
        Generates the HTML grid with the list of Greek gods and their local images,
        9 images per row.
        """
        gods = self.godsList()
        table_content = '        <div class="grid-container">\n'
        count = 0
        for god in gods:
            name = god.name
            local_img = god.local_img
            table_content += f'            <div class="grid-item">\n                <a href="/{name}">{name}</a><br>\n                <img src="images/{local_img}" alt="{name}">\n            </div>\n'
            count += 1
            if count % 9 == 0:
                table_content += (
                    '        </div>\n        <div class="grid-container">\n'
                )
        table_content += "        </div>\n"
        return table_content

    def generate_footer(self) -> str:
        """
        Generates the HTML footer section.
        """
        return """    </div>
</body>
</html>
"""

    def generate_index(
        self,
        file_path: str = "/tmp/index.html",
        logo_url: str = "https://www.compgen.de/wp-content/uploads/2019/01/CG-Logo02-340_156px-200x92.png",
    ) -> None:
        """
        Combines the header, table, and footer to generate the full HTML file (index.html).
        """
        header = self.generate_header(logo_url)
        table = self.generate_table()
        footer = self.generate_footer()

        with open(file_path, "w") as file:
            file.write(header + table + footer)

    def generate_apache_conf(self, output_path: str = "/tmp/playground.conf") -> None:
        """
        Generates the Apache configuration file for all wikis.
        Apache does the actual reverse proxying with ProxyPass
        which automatically strips the prefix when forwarding.
        """
        conf_content = f"""#
# Proxy configuration for Wiki Playgrounds
# generated by playground.py
# https://github.com/WolfgangFahl/genwiki2024/blob/main/genwiki/playground.py
#
<VirtualHost *:{self.apache_port}>
    ServerName {self.host}
    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-For "%{{REMOTE_ADDR}}s"
    """
        for idx, god in enumerate(self.godsList()):
            mw_port = self.base_port + (idx * self.step)
            conf_content += f"""    ProxyPass /{god.name} http://localhost:{mw_port}
    ProxyPassReverse /{god.name} http://localhost:{mw_port}
    """
        conf_content += """
    # Serve the overview page
    DocumentRoot /var/www/html

    CustomLog ${APACHE_LOG_DIR}/playground_access.log combined
    ErrorLog ${APACHE_LOG_DIR}/playground_error.log
</VirtualHost>
    """
        with open(output_path, "w") as f:
            f.write(conf_content)
        return output_path

    def generate_caddy_conf(self, output_path: str = "/tmp/Caddyfile") -> str:
        """
        Generates the Caddy configuration file.
        Caddy only handles TLS termination and forwards
        all traffic to Apache on localhost:80 which does
        the actual reverse proxying via ProxyPass.
        see https://github.com/WolfgangFahl/genwiki2024/issues/39
        """
        conf_content = f"""# TLS termination for Wiki Playgrounds
# generated by playground.py
# https://github.com/WolfgangFahl/genwiki2024/blob/main/genwiki/playground.py
# Caddy handles HTTPS only - Apache does the routing
# see https://github.com/WolfgangFahl/genwiki2024/issues/39

{self.host} {{
    reverse_proxy localhost:{self.apache_port}
}}
"""
        with open(output_path, "w") as f:
            f.write(conf_content)
        return output_path

    def generate_setup_script(self, output_path: str = "/tmp/setup_wikis.sh") -> None:
        """
        Generates a bash script to create and configure all wikis
        """
        script_content = """#!/bin/bash
# Setup script for Wiki Playgrounds
# generated by playground.py
# https://github.com/WolfgangFahl/genwiki2024/blob/main/genwiki/playground.py

set -e  # Exit on error
"""
        # First create all wikis
        for idx, god in enumerate(self.godsList()):
            mw_port = self.base_port + (idx * self.step)
            sql_port = mw_port + 1
            name = god.name
            script_content += f"""
echo "Setting up {name} wiki..."
profiwiki -rp -fu -cn {name} -bp {mw_port} -sp {sql_port} --all -f
"""
        with open(output_path, "w") as f:
            f.write(script_content)
        return output_path

    def generate_patch_script(self, output_path: str = "/tmp/patch_wikis.sh") -> str:
        """
        Generates a bash script to patch LocalSettings.php in all wiki containers.
        Sets wgScriptPath, wgArticlePath and wgServer correctly for each god.
        Uses printf to avoid bash $1 escaping issues in wgArticlePath.
        see https://github.com/WolfgangFahl/genwiki2024/issues/39
        """
        script_content = f"""#!/bin/bash
# Patch script for Wiki Playgrounds
# generated by playground.py
# see https://github.com/WolfgangFahl/genwiki2024/issues/39

LS=/var/www/html/LocalSettings.php
"""
        for god in self.godsList():
            name = god.name
            script_content += f"""
# {name}
docker exec "{name}-mw" sed -i 's#^\\$wgScriptPath = .*#\\$wgScriptPath = "/{name}";#' $LS
docker exec "{name}-mw" sed -i 's#^\\$wgServer = .*#\\$wgServer = "https://{self.host}";#' $LS
docker exec "{name}-mw" sed -i '/wgArticlePath/d' $LS
docker exec "{name}-mw" bash -c 'printf "\\n\\$wgArticlePath = \\"/{name}/index.php?title=\\$1\\";\\n" >> '$LS
echo "Patched {name}"
"""

        with open(output_path, "w") as f:
            f.write(script_content)
        return output_path


def main():
    parser = argparse.ArgumentParser(description="Wiki Playground Generator")
    parser.add_argument("--apache", action="store_true", help="Generate apache config")
    parser.add_argument("--caddy", action="store_true", help="Generate caddy config")
    parser.add_argument("--index", action="store_true", help="Generate index.html")
    parser.add_argument("--list", action="store_true", help="List the gods")
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Generate patch script (sets wgScriptPath, wgArticlePath, wgServer)",
    )
    parser.add_argument(
        "--setup", action="store_true", help="Generate the setup script"
    )
    parser.add_argument(
        "--host",
        default="wiki-playground.genealogy.net",
        help="Hostname for Caddy config and wgServer (default: wiki-playground.genealogy.net)",
    )
    args = parser.parse_args()

    pg = Playground(host=args.host)
    handled = False
    if args.index:
        pg.generate_index()
        pg.color_msg(GREEN, "✅ index.html generated.")
        handled = True
    if args.apache:
        conf = pg.generate_apache_conf()
        pg.color_msg(GREEN, f"✅ {conf} generated.")
        handled = True
    if args.caddy:
        conf = pg.generate_caddy_conf()
        pg.color_msg(GREEN, f"✅ {conf} generated.")
        handled = True
    if args.patch:
        patch = pg.generate_patch_script()
        pg.color_msg(GREEN, f"✅ {patch} generated.")
        handled = True
    if args.setup:
        setup = pg.generate_setup_script()
        pg.color_msg(GREEN, f"✅ {setup} generated.")
        handled = True
    if args.list:
        gods = pg.godsList()
        for god in gods:
            print(god.name)
        handled = True
    if not handled:
        parser.print_help()  # Replaces usage
        sys.exit(1)


if __name__ == "__main__":
    main()
