from azureml_user.parallel_run import EntryScript

#this may require installation of poppler https://github.com/Belval/pdf2image
from pdf2image import convert_from_path

#
def init():

    global png_folder
    global logger

    logger = EntryScript().logger
    logger.info("==> pdf_to_png init()")
    parser = argparse.ArgumentParser()
    parser.add_argument('--png-folder', type=str, dest='png_folder', help='png folder')
    args, unknown_args = parser.parse_known_args()
    
    png_folder = args.png_folder
    print("png_folder:", png_folder)

#
def run(mini_batch):
    
    logger.info("==> pdf_to_png run({}).".format(mini_batch))
    
    results = []
    for pdf_file_path in mini_batch:
        pdf_to_png(pdf_file_path)
        results.append(pdf_file_path)
        
    return results
    
#
def pdf_to_png(pdf_file_path):
    images = convert_from_path(pdf_file_path) #images is a list of each page of PDF as an image
    page_num = 1
    for image in images:
        png_name = os.path.join(png_folder,os.path.split(os.path.basename(pdf_file_path))[0],'_',str(page_num),'.png')
        image.save(png_name)
        page_num += 1