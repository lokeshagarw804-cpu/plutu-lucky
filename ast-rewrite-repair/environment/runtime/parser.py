"""
Expression parser for the simple language.

Parses assignment statements into AST nodes. Supports arithmetic
operators (+, -, *, /), variable references, numeric literals,
and conditional blocks.
"""


class ASTNode:
    """Base AST node."""
    _id_counter = 0

    def __init__(self, node_type, **kwargs):
        ASTNode._id_counter += 1
        self.node_id = ASTNode._id_counter
        self.node_type = node_type
        self.attrs = kwargs

    def to_dict(self):
        result = {"node_id": self.node_id, "type": self.node_type}
        for k, v in self.attrs.items():
            if isinstance(v, ASTNode):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [
                    item.to_dict() if isinstance(item, ASTNode) else item
                    for item in v
                ]
            else:
                result[k] = v
        return result


class Parser:
    """Parses source text into AST."""

    def parse_program(self, source):
        """Parse a program into a list of statement ASTs."""
        statements = []
        parts = source.split(";")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part.startswith("if "):
                stmt = self._parse_conditional(part)
            else:
                stmt = self._parse_assignment(part)
            if stmt:
                statements.append(stmt)
        return statements

    def _parse_assignment(self, text):
        """Parse 'var = expr' into an assignment node."""
        if "=" not in text:
            return None
        name, expr_text = text.split("=", 1)
        name = name.strip()
        expr = self._parse_expr(expr_text.strip())
        return ASTNode("assign", name=name, value=expr)

    def _parse_conditional(self, text):
        """Parse 'if cond: body' into a conditional node."""
        cond_body = text[3:]  # strip 'if '
        if ":" in cond_body:
            cond_text, body_text = cond_body.split(":", 1)
            cond = self._parse_expr(cond_text.strip())
            body = self._parse_assignment(body_text.strip())
            return ASTNode("if_stmt", condition=cond, body=body)
        return None

    def _parse_expr(self, text):
        """Parse an expression respecting operator precedence."""
        text = text.strip()
        return self._parse_additive(text)

    def _parse_additive(self, text):
        """Parse addition and subtraction (left-associative)."""
        # Find the rightmost + or - not inside parentheses
        depth = 0
        split_pos = -1
        split_op = None
        for i in range(len(text) - 1, -1, -1):
            ch = text[i]
            if ch == ')':
                depth += 1
            elif ch == '(':
                depth -= 1
            elif depth == 0 and ch in '+-' and i > 0:
                split_pos = i
                split_op = ch
                break

        if split_pos > 0:
            left = self._parse_additive(text[:split_pos])
            right = self._parse_multiplicative(text[split_pos + 1:])
            return ASTNode("binop", op=split_op, left=left, right=right)

        return self._parse_multiplicative(text)

    def _parse_multiplicative(self, text):
        """Parse multiplication and division (left-associative)."""
        text = text.strip()
        depth = 0
        split_pos = -1
        split_op = None
        for i in range(len(text) - 1, -1, -1):
            ch = text[i]
            if ch == ')':
                depth += 1
            elif ch == '(':
                depth -= 1
            elif depth == 0 and ch in '*/':
                split_pos = i
                split_op = ch
                break

        if split_pos > 0:
            left = self._parse_multiplicative(text[:split_pos])
            right = self._parse_atom(text[split_pos + 1:])
            return ASTNode("binop", op=split_op, left=left, right=right)

        return self._parse_atom(text)

    def _parse_atom(self, text):
        """Parse a literal number or variable reference."""
        text = text.strip()
        if text.startswith("(") and text.endswith(")"):
            return self._parse_expr(text[1:-1])
        try:
            val = float(text)
            if val == int(val) and "." not in text:
                return ASTNode("literal", value=int(text))
            return ASTNode("literal", value=val)
        except ValueError:
            # Check for comparison operators
            for op in [">", "<", ">=", "<=", "=="]:
                if op in text:
                    parts = text.split(op, 1)
                    left = self._parse_expr(parts[0])
                    right = self._parse_expr(parts[1])
                    return ASTNode("compare", op=op, left=left, right=right)
            return ASTNode("varref", name=text)
