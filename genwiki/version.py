"""
Created on 2024-08-15

@author: wf
"""

from dataclasses import dataclass

import genwiki


@dataclass
class Version(object):
    """
    Version handling for genwiki2024
    """

    name = "genwiki2024"
    version = genwiki.__version__
    date = "2024-08-15"
    updated = "2024-09-06"
    description = "genealogy Semantification"

    authors = "Wolfgang Fahl"

    doc_url = "https://wiki.bitplan.com/index.php/genwiki2024"
    chat_url = "https://github.com/WolfgangFahl/genwiki2024/discussions"
    cm_url = "https://github.com/WolfgangFahl/genwiki2024"

    license = f"""Copyright 2024 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""
    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
