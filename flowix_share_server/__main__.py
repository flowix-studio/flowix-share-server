# -*- coding: utf-8 -*-
import os, uuid, hashlib, sqlite3, bottle
from typing import Tuple
from beaker.middleware import SessionMiddleware
from beaker.session import Session
from . import __path__


_con:sqlite3.Connection = None
def _create_token() -> str:
    tokens = [
        row[0]
        for row in _con.execute("select `TOKEN` from `tokens`;").fetchall()
    ]
    
    token = hashlib.sha1(uuid.uuid4().hex.encode()).hexdigest()
    if token in tokens:
        token = _create_token()

    _con.execute(f"insert into `tokens` ( `TOKEN` ) values ( '{token}' );")
    _con.commit()

    return token

def _check_token(bottle_request:bottle.LocalRequest) -> Tuple[bool, str]:
    try:
        token = bottle_request.headers["flowix_token"]
    except KeyError:
        return False, None

    return _con.execute(f"select count(`TOKEN`) from `tokens` where `TOKEN`='{token}';").fetchone()[0] > 0, token

def _get_session(bottle_request:bottle.LocalRequest) -> Session:
    return bottle_request.environ.get("beaker.session")


_app = SessionMiddleware(bottle.app(), {
    "session.cookie_expires": 24 * 60 * 60 * 30
})


@bottle.get("/assets/<path:path>")
def get_static(path:str):
    return bottle.static_file(path, os.path.join(__path__[0], "assets"))

@bottle.get("/board")
@bottle.jinja2_view("board.html", template_lookup = [ os.path.join(__path__[0], "templates") ])
def fn_index_view():
    session = _get_session(bottle.request)
    if not session.has_key("user"):
        bottle.redirect("/login")

    return {
        "token_list": _con.execute("select * from `tokens`;").fetchall(),
        "shared_list": _con.execute("select * from `shared`;").fetchall()
    }
    
@bottle.post("/board")
def fn_index_api():
    return bottle.json_dumps({
        "token_list": _con.execute("select * from `tokens`;").fetchall(),
        "shared_list": _con.execute("select * from `shared`;").fetchall()
    })

@bottle.get("/login")
@bottle.jinja2_view("login.html", template_lookup = [ os.path.join(__path__[0], "templates") ])
def fn_login_view():
    if _con.execute("select count(*) from `users`;").fetchone()[0] == 0:
        bottle.redirect("/register")

    return {}

@bottle.post("/login")
def fn_login_api():
    datas = bottle.request.json or bottle.request.forms
    user, pwd = datas["id"], datas["pw"]

    if _con.execute(f"select count(*) from `users` where `ID`='{user}' and `PWD`='{pwd}';").fetchone()[0] == 0:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid `ID` or `PWD`!"
        })
    
    session = _get_session(bottle.request)
    session["user"] = {
        "login": True
    }
    session.save()
    
    return bottle.json_dumps({
        "state": "success"
    })

@bottle.get("/register")
@bottle.jinja2_view("register.html", template_lookup = [ os.path.join(__path__[0], "templates") ])
def fn_register_view():
    return {
        "user_exists": _con.execute("select count(*) from `users`;").fetchone()[0] > 0
    }
    
@bottle.post("/register")
def fn_register_api():
    datas = bottle.request.json or bottle.request.forms

    try:
        _con.execute(f"insert into `users` values ( '{datas['id']}', '{datas['pw']}' );")
        _con.commit()
        
        return bottle.json_dumps({
            "state": "success"
        })
    except Exception as e:
        return bottle.json_dumps({
            "state": "fail",
            "message": str(e)
        })


@bottle.post("/connect")
def fn_connect():
    return bottle.json_dumps({
        "token": _create_token()
    })

@bottle.post("/disconnect")
def fn_disconnect():
    exists, token = _check_token(bottle.request)
    if not exists:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid token!"
        })

    _con.execute(f"delete from `tokens` where `TOKEN`='{token}';")
    _con.commit()
    
    return bottle.json_dumps({
        "state": "success"
    })

@bottle.post("/share")
def fn_share():
    exists, _ = _check_token(bottle.request)
    if not exists:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid token!"
        })

    datas = bottle.request.json or bottle.request.forms
    try:
        manager_id = datas["manager"]
        share_id = datas["id"]
        obj_type = datas["type"]
        share_obj = datas["object"]
    except KeyError:
        return bottle.json_dumps({
            "state": "fail",
            "message": "`manager`, `id`, `type`, `object` must be specified!"
        })

    _con.execute(f"insert into `shared` ( `MANAGER`, `ID`, `TYPE`, `OBJECT` ) values ( '{manager_id}', '{share_id}', '{obj_type}', '{share_obj}' );")
    _con.commit()
    
    return bottle.json_dumps({
        "state": "success"
    })

@bottle.post("/delete/<manager_id>")
def fn_delete_multiple(manager_id:str):
    exists, _ = _check_token(bottle.request)
    if not exists:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid token!"
        })

    _con.execute(f"delete from `shared` where `MANAGER`='{manager_id}';")
    _con.commit()

    return bottle.json_dumps({
        "state": "success"
    })
    
@bottle.post("/delete/<manager_id>/<share_id>")
def fn_delete_single(manager_id:str, share_id:str):
    exists, _ = _check_token(bottle.request)
    if not exists:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid token!"
        })

    _con.execute(f"delete from `shared` where `MANAGER`='{manager_id}' and `ID`='{share_id}';")
    _con.commit()

    return bottle.json_dumps({
        "state": "success"
    })

@bottle.get("/share/<manager_id>")
def fn_get_share_multiple(manager_id:str):
    exists, _ = _check_token(bottle.request)
    if not exists:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid token!"
        })

    try:
        objects = [
            {
                "id": row[0],
                "type": row[1],
                "object": row[2]
            }
            for row in _con.execute(f"select `ID`, `TYPE`, `OBJECT` from `shared` where `MANAGER`='{manager_id}';").fetchall()
        ]
    except IndexError:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid id!"
        })
    
    return bottle.json_dumps({
        "state": "success",
        "objects": objects
    })

@bottle.get("/share/<manager_id>/<share_id>")
def fn_get_share(manager_id:str, share_id:str):
    exists, _ = _check_token(bottle.request)
    if not exists:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid token!"
        })

    row = _con.execute(f"select `TYPE`, `OBJECT` from `shared` where `MANAGER`='{manager_id}' and `ID`='{share_id}';").fetchone()
    if row is None:
        return bottle.json_dumps({
            "state": "fail",
            "message": "invalid id!"
        })

    return bottle.json_dumps({
        "state": "success",
        "object": {
            "type": row[0],
            "object": row[1]
        }
    })


def run_cli():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default = "127.0.0.1")
    parser.add_argument("--port", default = 8080, type = int)
    args = parser.parse_args()

    global _con
    _con = sqlite3.connect(os.path.join(__path__[0], ".flowix.share.server.db"))
    
    try:
        bottle.run(app = _app, host = args.host, port = args.port)
    except KeyboardInterrupt:
        pass
    
    _con.close()


if __name__ == "__main__":
    run_cli()
