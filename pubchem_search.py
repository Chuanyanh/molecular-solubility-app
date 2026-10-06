"""PubChem identity lookup only; it does not fetch experimental solubility."""
import json
import socket
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'

class PubChemSearchError(ValueError):
    pass

def _get_json(url):
    request = Request(url, headers={'User-Agent': 'MolecularSolubilityApp/2.0', 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=12) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        if error.code in (429, 503):
            raise PubChemSearchError('PubChem 暂时繁忙，请稍后重试。') from error
        raise PubChemSearchError(f'在线查询暂时失败（HTTP {error.code}）。') from error
    except (URLError, TimeoutError, socket.timeout) as error:
        raise PubChemSearchError('无法连接 PubChem 或查询超时。请检查网络；内置搜索仍可使用。') from error
    except (ValueError, UnicodeError) as error:
        raise PubChemSearchError('PubChem 返回内容无法读取，请稍后重试。') from error

def search_pubchem(query):
    query = query.strip()
    if not query:
        return []
    if len(query) > 200:
        raise PubChemSearchError('查询名称过长，请使用简短名称或 CID。')
    kind = 'cid' if query.isascii() and query.isdigit() else 'name'
    data = _get_json(f'{BASE}/compound/{kind}/{quote(query, safe="")}/cids/JSON')
    if not data:
        return []
    cids = data.get('IdentifierList', {}).get('CID', [])[:10]
    if not cids:
        return []
    identifiers = ','.join(str(int(cid)) for cid in cids)
    data = _get_json(f'{BASE}/compound/cid/{identifiers}/property/Title,MolecularFormula,SMILES/JSON')
    if not data:
        return []
    records = []
    for row in data.get('PropertyTable', {}).get('Properties', []):
        smiles = row.get('SMILES') or row.get('IsomericSMILES')
        if not smiles:
            continue
        cid = int(row['CID'])
        records.append(dict(id=f'pubchem:{cid}', cid=cid, name_zh='', name_en=row.get('Title', f'CID {cid}'),
                            aliases=[], smiles=smiles, formula=row.get('MolecularFormula', ''), source='PubChem',
                            source_url=f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}'))
    return records
