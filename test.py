print('Hello World')
def downloadFile(file,filename,sha):
    if os.path.exists(os.path.join(base_url,sha)):
        fileDirectory = os.path.join(base_url,sha,filename)
    else:
        os.makedirs(os.path.join(base_url,sha))
        fileDirectory = os.path.join(base_url,sha,filename)
    urllib.request.urlretrieve(file,fileDirectory)
    return fileDirectory

def get_repo_data(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        if not data:
            return Response({'message':'Json Data Missing'}, status=status.HTTP_400_BAD_REQUEST)
        userName = data.get('userName')
        req = requests.get(f'https://api.github.com/users/{userName}/repos')
        if req.status_code == 200:
            res = req.json()
            finalData = []
            for singleRes in res:
                finalData.append(singleRes.get('name'))
            return Response({'data':finalData},status=status.HTTP_200_OK)
        else:
            return Response({'data':req.json()},status=status.HTTP_200_OK)

@api_view(['POST'])
def get_branches_data(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        if not data:
            return Response({'message':'Json Data Missing'}, status=status.HTTP_400_BAD_REQUEST)
        userName = data.get('userName')
        repoName = data.get('repoName')
        req = requests.get(f'https://api.github.com/repos/{userName}/{repoName}/branches')
        if req.status_code == 200:
            res = req.json()
            finalData = []
            for singleRes in res:
                finalData.append(singleRes.get('name'))
            return Response({'data':finalData},status=status.HTTP_200_OK)
        else:
            return Response({'data':req.json()},status=status.HTTP_200_OK)

@api_view(['POST'])
def get_commit_data(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        if not data:
            return Response({'message':'No Data Received'}, status=status.HTTP_400_BAD_REQUEST)
        userName = data.get('userName')
        repoName = data.get('repoName')
        branchName = data.get('branchName')
        req = requests.get(f'https://api.github.com/repos/{userName}/{repoName}/branches/{branchName}')
        if req.status_code == 200:
            res = req.json()
            commitData = res.get('commit')
            parentData= commitData.get('parents')[0]
            parentSha = parentData.get('sha')
            reqData = requests.get(f'https://api.github.com/repos/{userName}/{repoName}/commits/{parentSha}')
            allParentPath = {}
            if reqData.status_code == 200:
                resData = reqData.json().get('files')
                for singleres in resData:
                    filePath = downloadFile(singleres.get('raw_url'),singleres.get('filename'),f'{userName}/{repoName}/parent')
                    allParentPath.update({singleres.get('filename'):singleres.get('raw_url')})
            parentKeys = allParentPath.keys()
            print('*********parentKeys*******')
            print(parentKeys)
            childSha = commitData.get('sha')
            reqData = requests.get(f'https://api.github.com/repos/{userName}/{repoName}/commits/{childSha}')
            if reqData.status_code == 200:
                resData = reqData.json().get('files')
                allFilesData = []
                for singleres in resData:
                    patchData = singleres.get('patch')
                    print(patchData)
                    finalLines = tk.tokenize(patchData)
                    linedeleted = []
                    lineadded = []
                    for singleline in finalLines[1:]:
                        if '-' == singleline[0]:
                            linedeleted.append(singleline[1:])
                        elif '+' == singleline[0]:
                            lineadded.append(singleline[1:])
                    send_data = []
                    if (linedeleted and lineadded):
                        if len(linedeleted) > len(lineadded):
                            count = len(linedeleted) - len(lineadded)
                            for i in range(len(lineadded)):
                                send_data.append({'line_deleted':linedeleted[i],'line_added':lineadded[i],'lineLanguage':guess.language_name(lineadded[i])})
                            for i in linedeleted[-count:]:
                                send_data.append({'line_deleted':i})
                        elif len(lineadded) > len(linedeleted):
                            count = len(lineadded) - len(linedeleted)
                            for i in range(len(linedeleted)):
                                send_data.append({'line_deleted':linedeleted[i],'line_added':lineadded[i],'lineLanguage':guess.language_name(lineadded[i])})
                            for i in lineadded[-count:]:
                                send_data.append({'line_added':i})
                        else:
                            for i in range(len(lineadded)):
                                send_data.append({'line_deleted':linedeleted[i],'line_added':lineadded[i],'lineLanguage':guess.language_name(lineadded[i])})
                    else:
                        if linedeleted:
                            for i in linedeleted:
                                send_data.append({'line_deleted':i,'lineLanguage':guess.language_name(i)})
                        elif lineadded:
                            for i in lineadded:
                                send_data.append({'line_added':i,'lineLanguage':guess.language_name(i)})
                    fileExtData = '\n'.join(lineadded)
                    codeLang = guess.language_name(fileExtData)


                    if singleres.get('filename') in parentKeys:
                        childfilePath = downloadFile(singleres.get('raw_url'),singleres.get('filename'),f'{userName}/{repoName}/child')
                        parentfilePath = downloadFile(allParentPath[singleres.get('filename')],singleres.get('filename'),f'{userName}/{repoName}/parent')
                        childCounter = 0
                        parentCounter = 0
                        childFile = open(childfilePath,"r")
                        childContent = childFile.read()
                        childCoList = childContent.split("\n")
                        parentFile = open(parentfilePath,"r")
                        parentContent = parentFile.read()
                        parentCoList = parentContent.split("\n")
                        for i in childCoList:
                            if i:
                                childCounter += 1
                        for i in parentCoList:
                            if i:
                                parentCounter += 1
                        print('***************childCounter********************')
                        print(childCounter)
                        print('***************parentCounter********************')
                        print(parentCounter)
                        finalCounter = childCounter - parentCounter
                        indivChanges = singleres.get('changes')
                        if finalCounter:
                            indivPercent = indivChanges / finalCounter
                        else:
                            indivPercent = 1
                        print('****************indivPercent******************')
                        print(indivPercent)
                        if codeLang in ['HTML','CSS']:
                            codeProb = (indivPercent / 70) * 100
                        else:
                            codeProb = (indivPercent / 100) * 100
                    else:
                        codeProb = (singleres.get('changes') / 70) * 100
                    if codeProb > 1:
                        codeProb = 100
                    else:
                        codeProb = codeProb * 100
                    allFilesData.append({"filename": singleres.get('filename'),"additions": singleres.get('additions'),\
                        "deletions": singleres.get('deletions'),"changes": singleres.get('changes'),'codeLanguage':codeLang,\
                            'changePercent':codeProb,'lines':send_data})
                return Response({'files_data':allFilesData},status=status.HTTP_200_OK)
            else:
                return Response({'data':reqData.json()},status=status.HTTP_200_OK)
        else:
            return Response({'data':req.json()},status=status.HTTP_200_OK)
