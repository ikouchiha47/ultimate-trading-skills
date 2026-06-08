"""Generic D3.js force-graph HTML renderer for dependency graphs.

Usage:
    from framework.viz import generate_graph_html
    generate_graph_html(
        graph_json=Path("graph/dependency_rippling.json"),
        output_dir=Path("viz/"),
        views={
            "ownership": ["investor_in", "founder_of", "director_of", "executive_of"],
            "ecosystem": ["supplies_to", "competes_with", "partners_with"],
            "social": ["founder_of", "director_of", "executive_of", "investor_in"],
        },
        title_prefix="Rippling",
    )

Produces one HTML file per view in output_dir with inline JSON (no fetch).
"""
from __future__ import annotations

import json
from pathlib import Path

# Default color map for relation types
RELATION_COLORS = {
    "investor_in": "#3498db",
    "supplies_to": "#2ecc71",
    "competes_with": "#e74c3c",
    "partners_with": "#9b59b6",
    "founder_of": "#f39c12",
    "director_of": "#1abc9c",
    "executive_of": "#e67e22",
    "depends_on": "#3498db",
    "customer_of": "#2ecc71",
    "group_entity": "#95a5a6",
    "board_interlock": "#1abc9c",
    "promoter_link": "#e67e22",
}

RELATION_LABELS = {
    "investor_in": "Investor → Company",
    "supplies_to": "Company → Customer",
    "competes_with": "Competitor",
    "partners_with": "Integration Partner",
    "founder_of": "Founder → Company",
    "director_of": "Director → Company",
    "executive_of": "Executive → Company",
    "depends_on": "Depends On",
    "customer_of": "Customer Of",
    "group_entity": "Group Entity",
    "board_interlock": "Board Interlock",
    "promoter_link": "Promoter Link",
}

# D3 HTML template (r-string to avoid f-string conflicts)
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#111;color:#eee;overflow:hidden}
#graph{width:100vw;height:100vh}
.legend{position:fixed;top:16px;right:16px;background:rgba(30,30,30,.92);padding:12px 16px;border-radius:8px;font-size:13px;z-index:10;border:1px solid #444;max-height:90vh;overflow-y:auto}
.legend h3{font-size:14px;margin-bottom:8px;color:#fff}
.legend label{display:flex;align-items:center;gap:6px;margin:3px 0;cursor:pointer;white-space:nowrap}
.legend input{cursor:pointer}
.csw{display:inline-block;width:12px;height:3px;border-radius:2px;margin-right:4px}
.nsw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.tooltip{position:fixed;background:rgba(20,20,20,.95);color:#eee;padding:10px 14px;border-radius:6px;font-size:12px;z-index:20;max-width:360px;border:1px solid #555;display:none;line-height:1.5;pointer-events:auto}
.tooltip a{color:#6cf}
.nlabel{font-size:9px;pointer-events:none;text-shadow:0 1px 2px #000;user-select:none;fill:#ddd}
.title{position:fixed;top:16px;left:16px;z-index:10;font-size:18px;font-weight:600;color:#fff}
.subtitle{position:fixed;top:40px;left:16px;z-index:10;font-size:11px;color:#999}
.tabs{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:4px;background:rgba(30,30,30,.92);padding:6px 10px;border-radius:8px;border:1px solid #444}
.tabs a{color:#aaa;text-decoration:none;padding:4px 12px;border-radius:4px;font-size:12px}
.tabs a.active{background:#3498db;color:#fff}
.tabs a:hover{background:#444;color:#fff}
</style>
</head>
<body>
<div class="title">{TITLE}</div>
<div class="subtitle">Drag nodes · Scroll to zoom · Hover for details · Checkboxes toggle edges</div>
<div id="graph"></div>
<div class="legend" id="legend"></div>
<div class="tooltip" id="tooltip"></div>
<div class="tabs">
{TABS}
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const DATA = JSON.parse({JSON});
const DEFAULT_VISIBLE = {VISIBLE};

const RC = {RELATION_COLORS};
const RL = {RELATION_LABELS};
const RD = {competes_with: "4,4", partners_with: "2,2"};

let vis = {};
for (const r of Object.keys(RC)) vis[r] = DEFAULT_VISIBLE.includes(r);

const nm = {};
const nd = DATA.nodes.map(d => { nm[d.id] = d; return {...d}; });
const lk = DATA.edges.map(e => ({source:e.src, target:e.dst, relation:e.relation, evidence:e.evidence, confidence:e.confidence}));

const W = window.innerWidth, H = window.innerHeight;
const svg = d3.select("#graph").append("svg").attr("width",W).attr("height",H);
const g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.1,6]).on("zoom",e=>g.attr("transform",e.transform)));

const sim = d3.forceSimulation(nd)
  .force("link", d3.forceLink(lk).id(d=>d.id).distance(d=>d.relation==="competes_with"?180:d.relation==="partners_with"?160:120))
  .force("charge", d3.forceManyBody().strength(-150))
  .force("center", d3.forceCenter(W/2,H/2))
  .force("collision", d3.forceCollide().radius(d=>d.id==="{CENTER_NODE}"?22:(d.kind==="person"?13:8)));

const ln = g.append("g").selectAll("line").data(lk).join("line")
  .attr("stroke",d=>RC[d.relation]||"#666")
  .attr("stroke-width",d=>d.confidence==="high"?2:1)
  .attr("stroke-dasharray",d=>RD[d.relation]||null)
  .attr("stroke-opacity",d=>vis[d.relation]?.7:.02);

const ng = g.append("g").selectAll("g.n").data(nd).join("g").attr("class","n")
  .call(d3.drag().on("start",(e,d)=>{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y}).on("drag",(e,d)=>{d.fx=e.x;d.fy=e.y}).on("end",(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null}));

ng.append("circle")
  .attr("r",d=>d.id==="{CENTER_NODE}"?18:(d.kind==="person"?10:(d.kind==="market"?6:7)))
  .attr("fill",d=>d.id==="{CENTER_NODE}"?"#e74c3c":(d.kind==="person"?"#f39c12":(d.kind==="market"?"#9b59b6":(d.domain==="venture capital"?"#2ecc71":"#3498db"))))
  .attr("stroke",d=>d.id==="{CENTER_NODE}"?"#fff":"rgba(255,255,255,.3)")
  .attr("stroke-width",d=>d.id==="{CENTER_NODE}"?3:1);

ng.append("text").attr("class","nlabel").attr("dy",d=>{const r=d.id==="{CENTER_NODE}"?18:(d.kind==="person"?10:7);return r+4}).attr("text-anchor","middle")
  .text(d=>d.name.length>16?d.name.slice(0,14)+"…":d.name);

let hideT;
function showTip(e,d){
  clearTimeout(hideT);
  const t=d3.select("#tooltip");
  let h=`<b>${d.name}</b>`;
  if(d.domain)h+=`<br><i>${d.domain}</i>`;
  if(d.kind==="market")h+=`<br><span style="color:#9b59b6">expansion adjacency</span>`;
  const rs=lk.filter(l=>(l.source.id||l.source)===d.id||(l.target.id||l.target)===d.id);
  if(rs.length){h+=`<hr style="border-color:#444;margin:4px 0">`;
    for(const r of rs.slice(0,7)){
      const si=r.source.id||r.source,ti=r.target.id||r.target;
      const o=si===d.id?(nm[ti]?.name||ti):(nm[si]?.name||si);
      h+=`<div style="font-size:11px">${RL[r.relation]||r.relation} → ${o}</div>`;
      if(r.evidence&&r.evidence[0]){
        h+=`<div style="font-size:10px;color:#aaa">${r.evidence[0].quote}</div>`;
        if(r.evidence[0].url)h+=`<a href="${r.evidence[0].url}" target="_blank">source</a> `;
      }
    }
    if(rs.length>7)h+=`<div style="color:#888">… +${rs.length-7} more</div>`;
  }
  t.html(h).style("display","block")
   .style("left",(e.clientX+14)+"px").style("top",(e.clientY-10)+"px");
  d3.select(this).select("circle").attr("stroke","#fff").attr("stroke-width",2);
}
function hideTip(){
  hideT=setTimeout(()=>{d3.select("#tooltip").style("display","none");},400);
}
function resetStroke(){
  d3.select(this).select("circle").attr("stroke",d=>d.id==="{CENTER_NODE}"?"#fff":"rgba(255,255,255,.3)").attr("stroke-width",d=>d.id==="{CENTER_NODE}"?3:1);
}

ng.on("mouseenter",showTip).on("mousemove",function(e){
  d3.select("#tooltip").style("left",(e.clientX+14)+"px").style("top",(e.clientY-10)+"px");
}).on("mouseleave",function(){hideTip();resetStroke.call(this);});

d3.select("#tooltip").on("mouseenter",()=>clearTimeout(hideT)).on("mouseleave",hideTip);

svg.append("defs").append("marker").attr("id","ar").attr("viewBox","0 -5 10 10").attr("refX",20).attr("refY",0).attr("markerWidth",6).attr("markerHeight",6).attr("orient","auto")
  .append("path").attr("d","M0,-5L10,0L0,5").attr("fill","#888");

sim.on("tick",()=>{ln.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);ng.attr("transform",d=>`translate(${d.x},${d.y})`);});

function ui(){
  ln.attr("stroke-opacity",d=>vis[d.relation]?.7:.02).attr("marker-end",d=>vis[d.relation]?"url(#ar)":"none");
  ng.select("circle").attr("opacity",d=>d.id==="{CENTER_NODE}"?1:lk.some(l=>vis[l.relation]&&((l.source.id||l.source)===d.id||(l.target.id||l.target)===d.id))?1:.08);
  ng.select("text").attr("opacity",d=>d.id==="{CENTER_NODE}"?1:lk.some(l=>vis[l.relation]&&((l.source.id||l.source)===d.id||(l.target.id||l.target)===d.id))?1:.05);
}

const leg=d3.select("#legend");
leg.html(`<h3>Relationships</h3>`);
for(const[r,c]of Object.entries(RC)){
  const lb=leg.append("label");
  lb.html(`<input type="checkbox" ${vis[r]?"checked":""}> <span class="csw" style="background:${c}"></span> ${RL[r]||r}`);
  lb.select("input").on("change",function(){vis[r]=this.checked;ui()});
}
leg.append("hr").style("border-color","#444").style("margin","6px 0");
for(const[c,l]of[["#e74c3c","{CENTER_NODE} (center)"],["#2ecc71","Investor (VC)"],["#3498db","Company"],["#f39c12","Person"],["#9b59b6","Market/Expansion"]]){
  leg.append("div").style("display","flex").style("align-items","center").style("gap","6px").style("font-size","11px").style("margin","2px 0")
    .html(`<span class="nsw" style="background:${c}"></span> ${l}`);
}
</script>
</body>
</html>"""


def generate_graph_html(
    graph_json: Path,
    output_dir: Path,
    views: dict[str, list[str]] | None = None,
    title_prefix: str = "",
    center_node: str | None = None,
    tab_files: dict[str, str] | None = None,
) -> list[Path]:
    """Generate D3 HTML files from a dependency graph JSON.

    Args:
        graph_json: Path to the dependency graph JSON (from DependencyGraph.save()).
        output_dir: Directory to write HTML files to.
        views: Dict mapping view name → list of relation types to show.
               If None, auto-detects from distinct relations in the data.
        title_prefix: Prefix for page titles (e.g. "Rippling").
        center_node: The central node ID for styling (default: first node in JSON).
        tab_files: Dict mapping view name → HTML filename for tab navigation.
                   If None, uses "{view}.html".

    Returns:
        List of written HTML file paths.
    """
    with open(graph_json) as f:
        data = json.load(f)

    # Auto-detect views if not provided
    if views is None:
        relations = set()
        for edge in data.get("edges", []):
            relations.add(edge.get("relation", ""))
        views = {"all": list(relations)}

    # Default center node
    if center_node is None:
        center_node = data["nodes"][0]["id"] if data.get("nodes") else "center"

    # Default tab files
    if tab_files is None:
        tab_files = {name: f"{name}.html" for name in views}

    # Double-dump JSON for safe JS string literal
    json_str = json.dumps(json.dumps(data))

    # Build relation color/label maps from data + defaults
    all_relations = set()
    for edge in data.get("edges", []):
        all_relations.add(edge.get("relation", ""))

    rc = {r: RELATION_COLORS.get(r, "#666") for r in all_relations}
    rl = {r: RELATION_LABELS.get(r, r) for r in all_relations}

    output_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for name, visible in views.items():
        title = f"{title_prefix} — {name.replace('_', ' ').title()}" if title_prefix else name.replace("_", " ").title()
        vis_json = json.dumps(visible)

        # Build tab navigation
        tabs_html = ""
        for vname, vfile in tab_files.items():
            active = ' class="active"' if vname == name else ""
            label = vname.replace("_", " ").title()
            tabs_html += f'<a href="{vfile}"{active}>{label}</a>\n'

        html = _HTML_TEMPLATE
        html = html.replace("{TITLE}", title)
        html = html.replace("{VISIBLE}", vis_json)
        html = html.replace("{JSON}", json_str)
        html = html.replace("{CENTER_NODE}", center_node)
        html = html.replace("{TABS}", tabs_html)
        html = html.replace("{RELATION_COLORS}", json.dumps(rc))
        html = html.replace("{RELATION_LABELS}", json.dumps(rl))

        out_path = output_dir / f"{name}.html"
        out_path.write_text(html)
        written.append(out_path)

    return written
