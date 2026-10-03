"""ChatGPT sandbox DOCX exports for the controlled Career Engine Markdown dialect.

Materialize this and assemble_brief_cv.py in the same private sandbox directory.
Requires python-docx/lxml, never invokes a shell, network, pip, or pandoc.
"""
import importlib.util
from pathlib import Path
import re


def inlines(text):
    if re.search(r'\[[^\]]*\]\(|!\[|`|<[^>]+>',text):
        raise ValueError('Unsupported inline Markdown; revise it instead of losing content')
    result=[]
    pattern=re.compile(r'\[([^\]]+)\]\{custom-style="([^"]+)"\}|\*\*([^*]+)\*\*|\*([^*]+)\*')
    def plain(value):
        for piece in re.split(r'(\s+)',value):
            if piece:
                result.append({'t':'Space'} if piece.isspace() else {'t':'Str','c':piece})
    pos=0
    for match in pattern.finditer(text):
        plain(text[pos:match.start()])
        if match.group(1) is not None:
            result.append({'t':'Span','c':[['',[],[['custom-style',match.group(2)]]],inlines(match.group(1))]})
        elif match.group(3) is not None:
            result.append({'t':'Strong','c':inlines(match.group(3))})
        else:
            result.append({'t':'Emph','c':inlines(match.group(4))})
        pos=match.end()
    plain(text[pos:])
    return result


def markdown_ast(text):
    lines=text.splitlines()
    blocks=[]
    i=0
    while i<len(lines):
        line=lines[i].strip()
        i+=1
        if not line:
            continue
        if line in ('<!-- SIDEBAR -->','<!-- /SIDEBAR -->'):
            blocks.append({'t':'RawBlock','c':['html',line]})
            continue
        if line.startswith(('```','~~~','|','<','>')) or re.match(r'^\s*\d+[.)]\s',line) or re.fullmatch(r'[-*_]{3,}',line):
            raise ValueError('Unsupported block Markdown; tables, code, HTML, and numbered lists require a reviewed conversion')
        heading=re.match(r'^(#{1,6})\s+(.+)$',line)
        if heading:
            blocks.append({'t':'Header','c':[len(heading.group(1)),['',[],[]],inlines(heading.group(2))]})
            continue
        div=re.fullmatch(r':::\s*\{custom-style="([^"]+)"\}',line)
        if div:
            body=[]
            while i<len(lines) and lines[i].strip()!=':::':
                body.append(lines[i]); i+=1
            if i==len(lines):
                raise ValueError('Unclosed custom-style div')
            i+=1
            blocks.append({'t':'Div','c':[['',[],[['custom-style',div.group(1)]]],markdown_ast('\n'.join(body))['blocks']]})
            continue
        if line.startswith(':::'):
            raise ValueError('Unsupported or unmatched custom-style div')
        if re.match(r'^[-*+]\s+',line):
            items=[]
            while True:
                items.append([{'t':'Para','c':inlines(re.sub(r'^[-*+]\s+','',line))}])
                if i>=len(lines) or not re.match(r'^[-*+]\s+',lines[i].strip()):
                    break
                line=lines[i].strip(); i+=1
            blocks.append({'t':'BulletList','c':items})
            continue
        paragraph=[line]
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|:::|<!--|[-*+]\s)',lines[i].strip()):
            if lines[i].strip().startswith(('```','~~~','|','<','>')) or re.match(r'^\d+[.)]\s',lines[i].strip()):
                raise ValueError('Unsupported block inside paragraph')
            paragraph.append(lines[i].strip()); i+=1
        blocks.append({'t':'Para','c':inlines(' '.join(paragraph))})
    return {'blocks':blocks}


def assembler():
    path=Path(__file__).with_name('assemble_brief_cv.py')
    if not path.is_file():
        raise FileNotFoundError('Attach and materialize assemble_brief_cv.py.txt beside this exporter')
    spec=importlib.util.spec_from_file_location('career_brief_assembler',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._pandoc_ast=markdown_ast
    return module


def brief_export(markdown,footer,template,output,*,name,tagline,contact):
    module=assembler()
    # Brief source uses styled divs; lists would be ignored by its upstream parser.
    ast=markdown_ast(markdown)
    allowed_styles={'SkillsHeading','Skills','RoleTitle','RoleActivitySingle'}
    section=None; sidebar=False
    for b in ast['blocks']:
        if b['t']=='RawBlock':
            sidebar=b['c'][1]=='<!-- SIDEBAR -->'
        elif b['t']=='Header':
            section=module._inline_text(b['c'][2]).upper()
            if b['c'][0]!=2 or section not in ('SKILLS','PROFILE SUMMARY','EXPERIENCE'):
                raise ValueError('Unsupported Brief heading')
        elif b['t']=='Div':
            style=dict(b['c'][0][2]).get('custom-style')
            body=b['c'][1]
            if style not in allowed_styles or len(body)!=1 or body[0]['t']!='Para':
                raise ValueError('Brief requires one paragraph per supported styled div')
            if not ((sidebar and style in ('SkillsHeading','Skills')) or (section=='EXPERIENCE' and style in ('RoleTitle','RoleActivitySingle'))):
                raise ValueError('Brief styled div is outside its required section')
        elif b['t']=='Para':
            if section not in ('PROFILE SUMMARY','EXPERIENCE'):
                raise ValueError('Brief paragraph is outside its required section')
        else:
            raise ValueError('Brief roles must use the upstream RoleActivitySingle div vocabulary')
    if footer:
        for b in markdown_ast(footer)['blocks']:
            if b['t'] not in ('Header','Para'):
                raise ValueError('Brief footer requires education/language paragraphs')
    parsed=module.parse_cv_markdown(markdown)
    sidebar=module.parse_footer_markdown(footer) if footer else {'education':[],'languages':''}
    data=dict(parsed,**sidebar,name=name,tagline=tagline,contact=contact,additional=None)
    module.fill_brief_cv(str(template),str(output),data)
    return Path(output)


def detailed_export(markdown,template,output,*,identity=None,tagline=None):
    module=assembler()
    doc=module.load_docx_or_dotx(str(template))
    ast=markdown_ast(markdown)
    for element in list(doc._element.body):
        if not element.tag.endswith('}sectPr'):
            doc._element.body.remove(element)
    def runs(paragraph,nodes,bold=False,italic=False,style=None):
        for node in nodes:
            t=node['t']
            if t in ('Str','Space'):
                run=paragraph.add_run(node.get('c',' '))
                run.bold=bold; run.italic=italic
                if style:
                    if style not in doc.styles:
                        raise ValueError('Missing template character style: '+style)
                    run.style=style
            elif t=='Strong':
                runs(paragraph,node['c'],True,italic,style)
            elif t=='Emph':
                runs(paragraph,node['c'],bold,True,style)
            elif t=='Span':
                runs(paragraph,node['c'][1],bold,italic,dict(node['c'][0][2]).get('custom-style'))
    def render(blocks,style=None):
        for block in blocks:
            t=block['t']
            if t=='RawBlock':
                continue
            if t=='Div':
                render(block['c'][1],dict(block['c'][0][2]).get('custom-style'))
                continue
            if t=='BulletList':
                for item in block['c']:
                    render(item,'List Bullet')
                continue
            paragraph_style=style
            nodes=block['c']
            if t=='Header':
                paragraph_style='Heading '+str(nodes[0]); nodes=nodes[2]
            if paragraph_style and paragraph_style not in doc.styles:
                raise ValueError('Missing template paragraph style: '+paragraph_style)
            paragraph=doc.add_paragraph(style=paragraph_style)
            runs(paragraph,nodes)
    render(ast['blocks'])
    def paragraphs(container):
        yield from container.paragraphs
        for table in container.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from paragraphs(cell)
    containers=[doc]
    for section in doc.sections:
        containers.extend([section.header,section.first_page_header,section.even_page_header,section.footer,section.first_page_footer,section.even_page_footer])
    for container in containers:
        for paragraph in paragraphs(container):
            # python-docx paragraph.runs omits hyperlink runs. Replace across
            # XML text nodes so split placeholders and contact links work too.
            nodes=paragraph._p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            text=''.join(node.text or '' for node in nodes)
            offsets=[]; offset=0
            for node in nodes:
                offsets.append(offset); offset+=len(node.text or '')
            for match in reversed(list(re.finditer(r'\{\{([^}]+)\}\}',text))):
                if match.group(1) not in (identity or {}):
                    continue
                start=next(i for i in reversed(range(len(nodes))) if offsets[i]<=match.start())
                end=next(i for i in reversed(range(len(nodes))) if offsets[i]<match.end())
                prefix=(nodes[start].text or '')[:match.start()-offsets[start]]
                suffix=(nodes[end].text or '')[match.end()-offsets[end]:]
                nodes[start].text=prefix+str(identity[match.group(1)])+(suffix if start==end else '')
                if start!=end:
                    for i in range(start+1,end):
                        nodes[i].text=''
                    nodes[end].text=suffix
            if tagline and container is not doc and paragraph.style.name=='Subtitle':
                paragraph.text=tagline
            if re.search(r'\{\{[^}]+\}\}',paragraph.text):
                raise ValueError('Unresolved template identity; supply the missing user data privately')
    doc.save(str(output))
    return Path(output)
