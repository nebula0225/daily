import os
import json

def check_dir(directory, file_name = ''):
    """
        if dose not exist directory create it and file
    """
    if not os.path.isdir(directory):
        os.mkdir(directory)
    
    if file_name != '':
        file_path = os.path.join(directory, file_name)

        if not os.path.isfile(file_path):
            with open(file_path, 'w', encoding='UTF-8') as f:
                if file_name.split(".")[1] == 'txt':
                    f.write("")
                elif file_name.split(".")[1] == 'json':
                    json.dump({}, f, indent = 4)
                else:
                    print("Only can create file that txt, json")
            print(f"The file {file_path} has been created.")
        else:
            return True
        
def open_json(locate, file_name):
    file_path = os.path.join(locate, file_name)
    with open(file_path, 'r', encoding="UTF-8") as j:
        json_file = json.loads(j.read())
    return json_file

def write_json(locate, file_name, dic):
    check_dir(locate, file_name)
    file_path = os.path.join(locate, file_name)
    with open(file_path, 'w', encoding="UTF-8") as f:
        f.writelines(json.dumps(dic, indent=4, default=str, ensure_ascii=False))
    print(f'write_json() : {file_name} / len : {len(list)}')
    return