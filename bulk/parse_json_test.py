'''
Copyright (c) 2019-2020 Cisco and/or its affiliates.
 
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). A copy of the License
can be found in the LICENSE.TXT file of this software or at
                 
https://developer.cisco.com/site/licenses/CISCO-SAMPLE-CODE-LICENSE-V1.0
 
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied.


Created on Dec 18, 2019
updated
'''
import parse_csv
import json
import unittest
import parse_json

class TestParseMethods(unittest.TestCase):
    
    def test_get_keys_from_dict(self):
        # get_keys_from_dict(my_dict, path_set, current_path=None, path_to_value_dict=None)
        pathset = set()
        mydict = {"field1":"value1",
                  "field2":"value2",
                  "field3": [1,2,3,4],
                  "field5": [{"nested1":"abc", "nested2":"bcd"},{"nested1":"xks", "nested2":"fgf"}],
                  "field6": [[1,2,3],[4,5,6]],
                  "field7": [[{"a":"b"},{"a":"q"}],[{"a":"z"},{"a":"r"}]]
                 }
        path_to_value_dict = {}
        parse_json.get_keys_from_dict(mydict, pathset, path_to_value_dict=path_to_value_dict)
        expected_key_set = set(['field1', 'field2', 'field3[0]','field3[1]','field3[2]','field3[3]', 
                               'field5[0].nested1', 'field5[0].nested2', 'field5[1].nested1', 'field5[1].nested2',
                               'field6[0][0]', 'field6[0][1]', 'field6[0][2]', 'field6[1][0]', 'field6[1][1]', 'field6[1][2]',
                               'field7[0][0].a', 'field7[0][1].a', 'field7[1][0].a', 'field7[1][1].a'])
        self.assertEqual(pathset, expected_key_set)
        expected_path_to_value_dict = {'field1':'value1', 'field2':'value2', 'field3[0]':1,'field3[1]':2,'field3[2]':3,'field3[3]':4, 
                               'field5[0].nested1':'abc', 'field5[0].nested2':'bcd', 'field5[1].nested1':'xks', 'field5[1].nested2':'fgf',
                               'field6[0][0]':1, 'field6[0][1]':2, 'field6[0][2]':3, 'field6[1][0]':4, 'field6[1][1]':5, 'field6[1][2]':6,
                               'field7[0][0].a':'b', 'field7[0][1].a':'q', 'field7[1][0].a':'z', 'field7[1][1].a':'r'}
        self.assertDictEqual(path_to_value_dict, expected_path_to_value_dict)

    def test_parse_json_to_csv_negative(self):
        # parse_json_to_csv(json_file_in, csv_file_out)
        found_exception = False
        try:
            parse_json.parse_json_to_csv('./bad_json_list.json', './outputfile.json')
        except ValueError:
            found_exception = True
        self.assertTrue(found_exception)
    
    
    def test_parse_json_to_csv_positive(self):
        # parse_json_to_csv(json_file_in, csv_file_out)
        # load raw json file
        parsed_object_list = None
        with open('./sample_json.json', encoding='utf-8-sig') as jsonfile:
            parsed_object_list = json.load(jsonfile)
        parse_json.parse_json_to_csv('./sample_json.json', './outputfile.csv')
        parsed_csv_list = parse_csv.parse_csv_to_dict('./outputfile.csv')
        self.assertEqual(parsed_object_list, parsed_csv_list)
        
    def test_parse_json_with_bool_positive(self):
        parsed_object_list = None
        with open('./test_json_wbool.json', encoding='utf-8-sig') as jsonfile:
            parsed_object_list = json.load(jsonfile)
        parse_json.parse_json_to_csv('./test_json_wbool.json', './outputfile.csv')
        parsed_csv_list = parse_csv.parse_csv_to_dict('./outputfile.csv')
        self.assertEqual(parsed_object_list, parsed_csv_list)

if __name__ == '__main__':
    unittest.main()