import os
from pyltp import SentenceSplitter, Segmentor, Postagger, Parser

addwords=['要','有','悬挂','挂','挂着','存在','增','加','摆','搁','增加','添加','想要','还要','放','放入','需要']
updatewords=['换','换成','改','改成']
deletewords=['删除','删','去掉','减','不','拿走']

add=[]
delete=[]
update=[]
addi = 0
deli = 0
upi = 0

class Item:
    def __init__(self):
        self.id = 0
        self.name = ''
        self.attr = []
        self.flag = -1
        self.next = 0

    def getresult(self):
        global add
        global delete
        global append
        global addi
        global deli
        global upi
        
        if(self.flag==0):
            
            #print(self.id)
            #add.append("添加")
            add.append([])
            add[addi].append(self.name)
            add[addi].append(self.attr)
            addi=addi+1
            

        if(self.flag==1):
            
            #delete.append("删除")
            delete.append([])
            delete[deli].append(self.name)
            delete[deli].append(self.attr)
            deli=deli+1

class LanguageAnalysis(object):
    def __init__(self, model_dir="./layoutmethods/ltp_data_v3.4.0"): 
        self.segmentor = Segmentor()  # 分词
        self.segmentor.load_with_lexicon(os.path.join(model_dir, "cws.model"),'dict/userdict')
        self.postagger = Postagger()  # 词性标注
        self.postagger.load(os.path.join(model_dir, "pos.model"))
        self.parser = Parser()  # 依存句法分析
        self.parser.load(os.path.join(model_dir, "parser.model"))

    def analyze(self, content):

        # 分句
        texts = SentenceSplitter.split(content)
        #print('\n'.join(texts))

        # 句子处理
        for text in texts:
            #print("————————————————————")
            #print("当前文本：{}".format(text))
            t=[]

            count=0
            for line in open("layoutmethods/ltp_data_v3.4.0/function.txt",encoding='utf-8-sig'):
                line=line.rstrip("\n")
                t.append(line.split('\t'))
                count=count+1

            #print(count)
            #print(t)    

            for i in range(0,len(text)):
                for j in range(len(text),i,-1):
    
                    subtext = text[i:j+1]
    
                    for k in range(count):
                        target=t[k][0]
                        if(subtext==target):
                            #print('1')
                            text=text.replace(subtext,t[k][1])
                            break
        
            #print(text)

            # 分词
            words = self.segmentor.segment(text)
            words_str = '\t'.join(words)
            total = len(words)
            #for i in range(words_total):
            #    results[0].append[i]
            #print("[分词]")
            #print(words_str)


            # 词性标注
            postags = self.postagger.postag(words)
            postags_str = '\t'.join(postags)
            #print("[词性标注]")
            #print(postags_str)

            # 依存句法分析
            arcs = self.parser.parse(words, postags)
            arcs_str = "\t".join("%d:%s" % (arc.head, arc.relation) for arc in arcs)
            #print("[依存句法分析]")
            #print(arcs_str)

            #求出句子中有多少个关键词
            count=0
            for i in range(total):
                if((postags[i]=='n') and ((arcs[i].relation=='VOB') or (arcs[i].relation=='POB') or (arcs[i].relation=='SBV') or (arcs[i].relation=='COO'))):
                    count=count+1

            #results=[[] for i in range(count)]
            #存放所有所需信息的列表
            wordlist=[]
            for i in range(count):
                wordlist.append(Item())
            #找到句子中的关键词（对象）
            k=0

            for i in range(total):
                if((postags[i]=='n') and ((arcs[i].relation=='VOB') or (arcs[i].relation=='POB') or (arcs[i].relation=='SBV'))):
                    #print(words[i])
                    wordlist[k].id=i+1
                    wordlist[k].name=words[i]
                    wordlist[k].next=arcs[i].head
                    #results[k].append(i+1)
                    #results[k].append(words[i])
                    k=k+1

        
            #print(results)
            #print("识别结果：",end="")
            #for i in range(k):
            #    print()
            #print(count)
            if(count>=2):
            # 0--添加 1--删除
                for j in range(k):
                    for i in range(total):
                        num = wordlist[j].next
                        if((i+1==num) and (words[i] in deletewords)):
                            wordlist[i].flag=1
                            #results[j].append(1)
                            break

                        if((i+1==num) and (words[i] not in deletewords) and (words[i] not in updatewords)):
                            wordlist[j].flag=0
                            #results[j].append(0)
                            break


            else:
                for j in range(k):
                    for i in range(total):
                        #if(arcs[i].relation=='HED'):
                        if(words[i] in deletewords):
                            wordlist[j].flag=1
                            break

                        if(words[i] not in deletewords and words[i] not in updatewords):
                            wordlist[j].flag=0
                            break


            # 同位语            
            for i in range(total):
                if((postags[i]=='n') and (arcs[i].relation=='COO')):
                    wordlist[k].id=i+1
                    wordlist[k].name=words[i]
                    wordlist[k].next=arcs[i].head    

                    for j in range(k):
                        #print(wordlist[j].id)
                        #print(arcs[i].head)
                        if(wordlist[j].id == arcs[i].head):
                            wordlist[k].flag = wordlist[j].flag
                    k=k+1
        
            # 2--修改
            flag=0
            for j in range(k):
                for i in range(total):
                    if((postags[i]=='v') and (words[i] in updatewords)):
                        wordlist[j].flag=2
                        flag=1
                        #results[j].append(2)
                        break
        
            #得到修饰关键词的词语
            for j in range(k):
                for i in range(total):
                    #num = results[j][0]
                    num = wordlist[j].id
                    if((arcs[i].head==num) and ((postags[i]=='b') or (postags[i]=='n')) and (arcs[i].relation=='ATT')):
                        #print(words[i])
                        wordlist[j].attr.append(words[i])        
                    if(arcs[i].relation=='COO'):
                        cindex = arcs[i].head
                        for r in range(len(wordlist[j].attr)):
                            if(wordlist[j].attr[r]==words[cindex-1]):
                                wordlist[j].attr.append(words[i])

                
            #模糊修饰词处理    ---后续改成列表---
            for i in range(count):
                for j in range(len(wordlist[i].attr)):
                    if(wordlist[i].attr[j]=='暖色'):
                        wordlist[i].attr[j]='红色/橙色/黄色'

                    if(wordlist[i].attr[j]=='冷色'):
                        wordlist[i].attr[j]='蓝色/绿色/紫色'


            new=''
            old=''
            
            if(flag==1):
                if(arcs[wordlist[0].id-1].relation=='VOB'):
                    new=wordlist[0].name
                    old=wordlist[1].name
                else:
                    old=wordlist[0].name
                    new=wordlist[1].name
                #update.append("修改")
                global upi
                update.append([])
                update[upi].append(old)
                update[upi].append(new)
                upi=upi+1
                
            else: 
                for i in range(k):
                    wordlist[i].getresult()

            #print(results)

            #for i in range(count):
            #    print('物品%d：%s    '%(i+1,results[i][1]),end="")

            #    print("操作：",end="")
            #    if(results[i][len(results[i])-1]==0):
            #        print("添加",end="")
            #    if(results[i][len(results[i])-1]==1):
            #        print("删除",end="")
            #    if(results[i][len(results[i])-1]==2):
            #        print("修改",end="")
            #    print("    ",end="")

            #    if(len(results[i])!=3):
            #        print('属性：',end="")
            #        for j in range(2,len(results[i])-1):                        
            #            print('%s'%results[i][j],end=" ")

            #    print('\n')


    def release_model(self):
        # 释放模型
        self.segmentor.release()
        self.postagger.release()
        self.parser.release()
    
    def clear(self):
        global add
        global delete
        global update
        global addi
        global deli
        global upi
        
        add=[]
        delete=[]
        update=[]
        addi=deli=upi=0
        
    def parserText(self, text):
        self.clear()
        self.analyze(text)
        re = [add, delete, update]

        return re