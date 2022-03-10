print('Hello World')
def downloadFile(file,filename,sha):
    if os.path.exists(os.path.join(base_url,sha)):
        fileDirectory = os.path.join(base_url,sha,filename)
    else:
        os.makedirs(os.path.join(base_url,sha))
        fileDirectory = os.path.join(base_url,sha,filename)
    urllib.request.urlretrieve(file,fileDirectory)
    return fileDirectory
