from django.shortcuts import render
from .hmfrm import hfrm
import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseNotAllowed
from .util.imgutil import analyse_file, extr_exif, byte_anal
from .mongo import collection
import datetime
from copy import deepcopy
def home(request):
    frm=hfrm()
    return render(request, "app/home.html", {"form":frm})
def sanitize(val):
    if isinstance(val, dict):
        return {str(k): sanitize(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize(v) for v in val]
    elif isinstance(val, tuple):
        return tuple(sanitize(v) for v in val)
    elif hasattr(val, 'numerator') and hasattr(val, 'denominator'):
        # specifically catch IFDRational-like objects
        return str(val)
    elif isinstance(val, (int, float, str, bool)) or val is None:
        return val
    else:
        return str(val)

def redir(request):
    if(request.method=="POST"):
        frm=hfrm(request.POST, request.FILES)
        if frm.is_valid():
            mod=request.POST.get("mod")
            fileinput=request.FILES["filepth"]
            fs=FileSystemStorage()
            fname=fs.save(fileinput.name, fileinput)
            fpath=fs.path(fname)
            if mod=="detailsmod":
                result=analyse_file(fpath)
                title="File Analysis report"
                os.remove(fpath)
            elif mod=="exifmod":
                result=extr_exif(fpath)
                title="File EXIF Analysis report"
                os.remove(fpath)
            elif mod=="bytemod":
                result=byte_anal(fpath)
                title="File Byte Stream Analysis report"
                os.remove(fpath)
            result=sanitize(result)
            collection.insert_one({
                "title": title,
                "result": result,
                "timestamp": datetime.datetime.now()
            })
            
            return render(request, "app/output.html", {"res":result, "tit":title})
    else:
        return HttpResponseNotAllowed(["POST"])

def history_view(request):
    docs = list(collection.find().sort("timestamp", -1))
    history = []
    for doc in docs:
        history.append({
            "id": str(doc["_id"]),
            "tit": doc["title"],
            "res": doc["result"]
        })
    return render(request, "app/history.html", {"history": history, "tit": "Analysis History"})