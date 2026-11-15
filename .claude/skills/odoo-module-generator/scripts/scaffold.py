#!/usr/bin/env python3
"""Generate an OCA-style Odoo addon skeleton (default target: Odoo 19.0).

Usage examples:
    python scaffold.py library_management --model library.book --model library.author
    python scaffold.py sale_order_approval --depends sale --inherit-only --dest ./addons

The output installs as-is (models, ACLs, groups, views, menus, a test and the
readme/ fragments). The generated code is a starting point: review it and
remove what the module does not need.
"""

from __future__ import annotations

import argparse
import keyword
import re
import sys
from datetime import date
from pathlib import Path

LICENSE_URLS = {
    "AGPL-3": ("AGPL-3.0 or later", "https://www.gnu.org/licenses/agpl"),
    "LGPL-3": ("LGPL-3.0 or later", "https://www.gnu.org/licenses/lgpl"),
}


def header(author: str, license_key: str) -> str:
    text, url = LICENSE_URLS[license_key]
    return f"# Copyright {date.today().year} {author}\n# License {text} ({url}).\n"


def class_name(model: str) -> str:
    return "".join(part.capitalize() for part in model.split("."))


def xml_model(model: str) -> str:
    return model.replace(".", "_")


def build(args: argparse.Namespace) -> dict[str, str]:
    mod, ver, hdr = args.name, args.version, header(args.author, args.license)
    models = [] if args.inherit_only else (args.model or [f"{mod.replace('_', '.')}"])
    files: dict[str, str] = {}

    data = [f"security/{mod}_security.xml"] if models else []
    data += ["security/ir.model.access.csv"] if models else []
    data += [f"views/{xml_model(m)}_views.xml" for m in models]
    data += ["views/menus.xml"] if models else []
    data_list = "".join(f'        "{d}",\n' for d in data)
    app_line = '    "application": True,\n' if models and args.application else ""
    depends = ", ".join(f'"{d}"' for d in args.depends)
    files["__manifest__.py"] = f'''{hdr}{{
    "name": "{mod.replace("_", " ").title()}",
    "summary": "TODO: one line describing the business value",
    "version": "{ver}.1.0.0",
    "category": "Uncategorized",
    "website": "{args.website}",
    "author": "{args.author}",
    "license": "{args.license}",
    "development_status": "Alpha",
{app_line}    "depends": [{depends}],
    "external_dependencies": {{"python": []}},
    "data": [
{data_list}    ],
}}
'''
    files["__init__.py"] = "from . import models\n" if models else ""
    files["models/__init__.py"] = "".join(
        f"from . import {xml_model(m)}\n" for m in sorted(models)
    )

    acl = [
        "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"
    ]
    for m in models:
        xm = xml_model(m)
        files[f"models/{xm}.py"] = f'''{hdr}from odoo import api, fields, models
from odoo.exceptions import ValidationError


class {class_name(m)}(models.Model):
    _name = "{m}"
    _description = "{class_name(m)}"
    _order = "name"
    _check_company_auto = True

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )
    note = fields.Text()

    _name_company_uniq = models.Constraint(
        "UNIQUE (name, company_id)",
        "The name must be unique per company.",
    )

    @api.constrains("name")
    def _check_name(self) -> None:
        for record in self:
            if record.name and not record.name.strip():
                raise ValidationError(self.env._("The name cannot be blank."))
'''
        files[f"views/{xm}_views.xml"] = f'''<?xml version="1.0" encoding="utf-8" ?>
<odoo>
    <record id="{xm}_view_list" model="ir.ui.view">
        <field name="name">{m}.view.list</field>
        <field name="model">{m}</field>
        <field name="arch" type="xml">
            <list>
                <field name="name" />
                <field name="company_id" groups="base.group_multi_company" />
            </list>
        </field>
    </record>
    <record id="{xm}_view_form" model="ir.ui.view">
        <field name="name">{m}.view.form</field>
        <field name="model">{m}</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <widget name="web_ribbon" title="Archived" bg_color="text-bg-danger"
                        invisible="active" />
                    <group>
                        <field name="name" />
                        <field name="company_id" groups="base.group_multi_company" />
                        <field name="active" invisible="1" />
                    </group>
                    <field name="note" placeholder="Notes..." />
                </sheet>
            </form>
        </field>
    </record>
    <record id="{xm}_view_search" model="ir.ui.view">
        <field name="name">{m}.view.search</field>
        <field name="model">{m}</field>
        <field name="arch" type="xml">
            <search>
                <field name="name" />
                <filter string="Archived" name="inactive" domain="[('active', '=', False)]" />
            </search>
        </field>
    </record>
    <record id="{xm}_action" model="ir.actions.act_window">
        <field name="name">{class_name(m)}</field>
        <field name="res_model">{m}</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
'''
        acl.append(f"access_{xm}_user,{m} user,model_{xm},group_{mod}_user,1,1,1,0")
        acl.append(
            f"access_{xm}_manager,{m} manager,model_{xm},group_{mod}_manager,1,1,1,1"
        )

    if models:
        files["security/ir.model.access.csv"] = "\n".join(acl) + "\n"
        title = mod.replace("_", " ").title()
        rules = "".join(
            f'''    <record id="{xml_model(m)}_rule_company" model="ir.rule">
        <field name="name">{m}: multi-company</field>
        <field name="model_id" ref="model_{xml_model(m)}" />
        <field name="domain_force">[('company_id', 'in', company_ids)]</field>
    </record>
'''
            for m in models
        )
        files[
            f"security/{mod}_security.xml"
        ] = f"""<?xml version="1.0" encoding="utf-8" ?>
<odoo>
    <record id="res_groups_privilege_{mod}" model="res.groups.privilege">
        <field name="name">{title}</field>
    </record>
    <record id="group_{mod}_user" model="res.groups">
        <field name="name">User</field>
        <field name="sequence">10</field>
        <field name="privilege_id" ref="res_groups_privilege_{mod}" />
        <field name="implied_ids" eval="[Command.link(ref('base.group_user'))]" />
    </record>
    <record id="group_{mod}_manager" model="res.groups">
        <field name="name">Administrator</field>
        <field name="sequence">20</field>
        <field name="privilege_id" ref="res_groups_privilege_{mod}" />
        <field name="implied_ids" eval="[Command.link(ref('group_{mod}_user'))]" />
        <field name="user_ids" eval="[Command.link(ref('base.user_admin'))]" />
    </record>
{rules}</odoo>
"""
        items = "".join(
            f'''    <menuitem id="{xml_model(m)}_menu" parent="{mod}_menu_root"
        action="{xml_model(m)}_action" sequence="{10 * (i + 1)}" />
'''
            for i, m in enumerate(models)
        )
        files["views/menus.xml"] = f'''<?xml version="1.0" encoding="utf-8" ?>
<odoo>
    <menuitem id="{mod}_menu_root" name="{title}" groups="group_{mod}_user" sequence="50" />
{items}</odoo>
'''
        first = models[0]
        files["tests/__init__.py"] = f"from . import test_{xml_model(first)}\n"
        files[
            f"tests/test_{xml_model(first)}.py"
        ] = f'''{hdr}from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class Test{class_name(first)}(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.user = new_test_user(
            cls.env, login="{mod}_user", groups="{mod}.group_{mod}_user"
        )
        cls.outsider = new_test_user(
            cls.env, login="{mod}_outsider", groups="base.group_user"
        )

    def test_user_can_create(self):
        record = self.env["{first}"].with_user(self.user).create({{"name": "Test"}})
        self.assertEqual(record.company_id, self.env.company)

    def test_user_cannot_delete(self):
        record = self.env["{first}"].create({{"name": "Test"}})
        with self.assertRaises(AccessError):
            record.with_user(self.user).unlink()

    def test_outsider_has_no_access(self):
        with self.assertRaises(AccessError):
            self.env["{first}"].with_user(self.outsider).search([])
'''
    files["readme/DESCRIPTION.md"] = (
        "TODO: what the module does and why (business value).\n"
    )
    files["readme/USAGE.md"] = "TODO: step-by-step usage for the end user.\n"
    files["readme/CONTRIBUTORS.md"] = f"- {args.author}\n"
    files["i18n/.gitkeep"] = ""
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "name", help="technical name in snake_case, e.g. sale_order_approval"
    )
    parser.add_argument(
        "--model", action="append", help="new model, repeatable (a.b.c)"
    )
    parser.add_argument("--depends", nargs="+", default=["base"])
    parser.add_argument("--version", default="19.0", help="Odoo series, e.g. 19.0")
    parser.add_argument("--author", default="Daniel Cejudo Echeverry")
    parser.add_argument("--license", choices=sorted(LICENSE_URLS), default="LGPL-3")
    parser.add_argument("--website", default="https://github.com/DCEtech")
    parser.add_argument("--dest", default=".", help="addons directory")
    parser.add_argument("--application", action="store_true")
    parser.add_argument(
        "--inherit-only", action="store_true", help="no new models (extension module)"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite existing folder"
    )
    args = parser.parse_args(argv)

    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.name) or keyword.iskeyword(args.name):
        parser.error("name must be snake_case and a valid Python identifier")
    for model in args.model or []:
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z0-9_]+)+", model):
            parser.error(f"invalid model name: {model}")

    root = Path(args.dest) / args.name
    if root.exists() and not args.force:
        print(f"{root} already exists (use --force to overwrite)", file=sys.stderr)
        return 1
    for rel, content in build(args).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"created {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
