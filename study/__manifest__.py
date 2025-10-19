# -*- coding: utf-8 -*-
{
    "name": "Модуль для учёбы ЧувГУ",
    "summary": "ЧувГУ. Модуль для учёбы",
    "description": "ЧувГУ. Модуль для учебы в ЧувГУ",
    "author": "Назаров Ярослав",
    "website": "https://alkona.it",
    "category": "ЧувГУ / Модуль для учёбы",
    "version": "0.1",
    "depends": ["base", "web"],
    "application": True,
    "data": [
        "views/game.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "study/static/src/**/*",
        ],
    },
    "demo": [],
    'license': 'AGPL-3',
}
