import markdown
from html.parser import HTMLParser

class DOMBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = []
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'children': []}
        # Remove empty attrs
        if not node['attrs']:
            del node['attrs']
        
        # Add to current parent
        current = self.stack[-1]
        if isinstance(current, list):
            current.append(node)
        else:
            # If the current top is a dictionary (node), add to its children
            if 'children' not in current:
                current['children'] = []
            current['children'].append(node)
        
        # Push to stack
        if tag not in ['br', 'img', 'hr', 'meta', 'link']: # Void elements
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag not in ['br', 'img', 'hr', 'meta', 'link']:
            if len(self.stack) > 1:
                self.stack.pop()

    def handle_data(self, data):
        if not data:
            return
        current = self.stack[-1]
        if isinstance(current, list):
            current.append(data)
        else:
            if 'children' not in current:
                current['children'] = []
            current['children'].append(data)

def markdown_to_nodes(md_text):
    if not md_text:
        return []
    html = markdown.markdown(md_text)
    builder = DOMBuilder()
    builder.feed(html)
    return builder.root

def nodes_to_markdown(nodes):
    if not nodes:
        return ""
    
    md_output = []
    
    for node in nodes:
        if isinstance(node, str):
            md_output.append(node)
            continue
            
        tag = node.get('tag')
        children = node.get('children', [])
        # Recursively process children
        # But for lists we need special handling
        
        if tag == 'p':
            md_output.append(f"{nodes_to_markdown(children)}\n\n")
        elif tag == 'h3':
            md_output.append(f"### {nodes_to_markdown(children)}\n\n")
        elif tag == 'h4':
            md_output.append(f"#### {nodes_to_markdown(children)}\n\n")
        elif tag in ['b', 'strong']:
            md_output.append(f"**{nodes_to_markdown(children)}**")
        elif tag in ['i', 'em']:
            md_output.append(f"*{nodes_to_markdown(children)}*")
        elif tag == 'u':
            md_output.append(f"<u>{nodes_to_markdown(children)}</u>")
        elif tag == 's':
             md_output.append(f"~~{nodes_to_markdown(children)}~~")
        elif tag == 'a':
            href = node.get('attrs', {}).get('href', '')
            md_output.append(f"[{nodes_to_markdown(children)}]({href})")
        elif tag == 'img':
            src = node.get('attrs', {}).get('src', '')
            md_output.append(f"![image]({src})\n\n")
        elif tag == 'ul':
            for child in children:
                if isinstance(child, dict) and child.get('tag') == 'li':
                    li_content = nodes_to_markdown(child.get('children', []))
                    md_output.append(f"- {li_content}\n")
            md_output.append("\n")
        elif tag == 'ol':
            idx = 1
            for child in children:
                if isinstance(child, dict) and child.get('tag') == 'li':
                    li_content = nodes_to_markdown(child.get('children', []))
                    md_output.append(f"{idx}. {li_content}\n")
                    idx += 1
            md_output.append("\n")
        elif tag == 'code':
            md_output.append(f"`{nodes_to_markdown(children)}`")
        elif tag == 'pre':
            md_output.append(f"```\n{nodes_to_markdown(children)}\n```\n\n")
        elif tag == 'br':
            md_output.append("  \n")
        elif tag == 'hr':
            md_output.append("---\n\n")
        elif tag == 'blockquote':
            inner_text = nodes_to_markdown(children)
            lines = inner_text.split('\n')
            quoted = '\n'.join([f"> {line}" for line in lines if line.strip()])
            md_output.append(f"{quoted}\n\n")
        elif tag == 'li':
            # Should be handled by parent, but if standalone:
            md_output.append(f"- {nodes_to_markdown(children)}\n")
        else:
            # Fallback
            md_output.append(nodes_to_markdown(children))

    return "".join(md_output)
