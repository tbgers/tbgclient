"""Handles low-level API calls."""

from . import TBGException
import requests

silent = False


class SessionMultiple(requests.Session):
    """An extension of requests.Session, allowing multiple sessions to be
    used at once without interfering with each other.
    """
    def __init__(self):
        self._cookies = requests.cookies.RequestsCookieJar()
        requests.Session.__init__(self)
        
    def request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):
        """Constructs a :class:`Request <Request>`, prepares it and sends it.
        Returns :class:`Response <Response>` object.

        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query
            string for the :class:`Request`.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the
            :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the
            :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the
            :class:`Request`.
        :param files: (optional) Dictionary of ``'filename': file-like-objects``
            for multipart encoding upload.
        :param auth: (optional) Auth tuple or callable to enable
            Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Set to True by default.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol or protocol and
            hostname to the URL of the proxy.
        :param stream: (optional) whether to immediately download the response
            content. Defaults to ``False``.
        :param verify: (optional) Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to ``True``.
        :param cert: (optional) if String, path to ssl client cert file (.pem).
            If Tuple, ('cert', 'key') pair.
        :rtype: requests.Response
        """
        # Create the Request.
        req = requests.Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies or self._cookies,
            hooks=hooks,
        )
        prep = self.prepare_request(req)

        proxies = proxies or {}

        settings = self.merge_environment_settings(
            prep.url, proxies, stream, verify, cert
        )

        # Send the request.
        send_kwargs = {
            'timeout': timeout,
            'allow_redirects': allow_redirects,
        }
        send_kwargs.update(settings)
        resp = self.send(prep, **send_kwargs)
        self._cookies.update(resp.cookies)
        # print(self._cookies)
        return resp


def post_post(session, post, tid, **kwargs):
    req = session.post(f"https://tbgforums.com/forums/post.php?tid={tid}", {"req_message": post, "form_sent": 1}, **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at POST")
    return session, req


def get_post(session, pid, **kwargs):
    req = session.get(f"https://tbgforums.com/forums/viewtopic.php?pid={pid}", **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at GET")
    return session, req


def delete_post(session, pid, **kwargs):
    req = session.post(f"https://tbgforums.com/forums/delete.php?id={pid}", data={"delete": "Delete"}, **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at POST")
    return session, req


def get_topic(session, tid, page=1, **kwargs):
    req = session.get(f"https://tbgforums.com/forums/viewtopic.php?id={tid}&p={page}", **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at GET")
    return session, req
    
    
def get_forum(session, fid, page=1, **kwargs):
    req = session.get(f"https://tbgforums.com/forums/viewforum.php?id={fid}&p={page}", **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at GET")
    return session, req
    

def login(session, user, password, **kwargs):
    req = session.post(f"https://tbgforums.com/forums/login.php?action=in",
                       {"req_username": user, "req_password": password, "form_sent": "1", "login": "Login"}, 
                       **kwargs
                       )
    if req.status_code >= 400:
        raise TBGException.RequestException(f"Got {req.status_code} at login", **kwargs)
    return session, req


def get_user(session, uid, **kwargs):
    req = session.get(f"https://tbgforums.com/forums/profile.php?id={uid}", **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at GET")
    return session, req


def search(session, query, author="", search_in=0, forums=[], sort=0, direction=-1, show_as="topics", **kwargs):
    direction = "DESC" if direction < -1 else "ASC"
    req = session.get(
        f"https://tbgforums.com/forums/search.php?action=search&" +
        f"keywords={query}&author={author}&search_in={search_in}&sort_by={sort}&" +
        "&".join(f"forums[]={x}" for x in forums) + 
        f"&sort_dir={direction}&show_as={show_as}&search=Submit",
        **kwargs)
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at GET")
    return session, req


def get_message(session, channel, lastID=0, getInfo: tuple = tuple(), **kwargs):
    req = session.get(
        "https://tbgforums.com/forums/chat/?ajax=true&" +
        f"lastID={lastID}&" +
        f"getInfos={','.join(getInfo)}&" + 
        f"channelID={channel}",
        **kwargs
    )
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at GET")
    return session, req


def post_message(session, message, lastID=0, **kwargs):
    req = session.post(
        "https://tbgforums.com/forums/chat/?ajax=true",
        {"lastID": str(lastID), "text": message},
        **kwargs
    )
    if req.status_code > 400 and not silent:
        raise TBGException.RequestException(f"Got {req.status_code} at POST")
    return session, req
