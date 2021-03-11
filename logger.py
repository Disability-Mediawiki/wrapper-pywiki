from datetime import datetime
import configparser


class DebugLogger :
    def __init__(self):
        # self.itsProblem = "problem"
        self.config = configparser.ConfigParser()
        self.config.read('config/application.config.ini')

    def logError(self,class_name, exception, exc_type, exc_obj, exc_tb , tb, err_message=None):
        err_trace = f"ERROR_TRACE >>>: + {exc_type} , method: {tb[2]} , line-no: {tb[1]}"
        if(err_message is None):
            err_list = [f"Class : {class_name} \n", f"{err_trace} \n", f"ERROR >> {exception} \n",
                        f"{datetime.now()} \n\n"]
        else:
            err_list=[f"Class : {class_name} \n", f"{err_message} \n", f"{err_trace} \n",
                      f"ERROR >> {exception} \n", f"{datetime.now()} \n\n"]

        file1 = open(self.config.get('application', 'error_log'), 'a')
        file1.writelines(err_list)
        file1.close()
