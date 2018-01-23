import json
import codecs


def main():
    in_json1 = './limai_focus_raw1.json'
    in_json2 = './limai_focus_raw.json'
    out_json = './limai_focus_raw1_new.json'
    with codecs.open(in_json1, 'r', encoding='utf-8') as in_file1:
      with codecs.open(in_json2, 'r', encoding='utf-8') as in_file2:
        with codecs.open(out_json, 'w', encoding='utf-8') as out_file:
            data = json.load(in_file1)
            #data.extend(json.load(in_file2))
            print(len(data))
            count = 1
            max_len = len(data)
            for case in data:
                s = json.dumps(case, ensure_ascii=False)
                if count == 1:
                    out_file.write('[%s,\n' % s)
                elif count == max_len:
                    out_file.write('%s]' % s)
                else:
                    out_file.write('%s,\n' % s)
                count += 1


if __name__ == "__main__":
    main()

