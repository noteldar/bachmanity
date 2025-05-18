from dataclasses import dataclass
from typing import List


@dataclass
class Founder:
    name: str
    background: str


@dataclass
class Startup:
    vision: str
    company_name: str
    founders: List[Founder]
    product_description: str


@dataclass
class VCPartner:
    name: str
    fund_name: str
    fund_website: str
    linkedin_url: str


@dataclass
class DrafterDeps:
    startup: Startup
    vc_partner: VCPartner
