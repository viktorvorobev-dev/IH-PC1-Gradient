#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import imageio.v2 as imageio
from matplotlib import pyplot as plt
import pandas as pd
import cv2 
from sklearn.decomposition import PCA as sklearnPCA
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import FastICA
from skimage.filters import gaussian
import os
import PySimpleGUI as sg
from PIL import Image
from io import BytesIO
import io
import seaborn as sns
from tqdm import tqdm
from skimage import morphology

# In[2]:


def upload(name):
    layout = [[sg.Text('Choose Folders with Files for ' + str(name) + ' patient:')],
              [sg.Text('Folder with skin photos:', size=(22, 1)), sg.InputText(), sg.FolderBrowse()],
              [sg.Submit(), sg.Cancel()]]
    window = sg.Window('Photos upload', layout)
    event, values = window.read()
    window.close()
    
    for current_dir, next_dir, files in os.walk(values[0], topdown=True):
        continue
        
    gray = lambda rgb : np.dot(rgb[... , :3] , [1. , 1., 1. ])    
    images_cube = np.array((gray(imageio.imread(current_dir + '/' + files[i])) for i in range(8)))
#     hypercube_of_images = np.dstack((tuple(images_cube)))
    return images_cube#hypercube_of_images


# In[3]:


def crop_image(hypercube_of_images, name):
    w_name = "Contour Determination"
    
    def motion():
        return f'X, Y = {window.user_bind_event.x, window.user_bind_event.y}'
    
    def update_spinners():
        if x1 is None:
            window["click_coordinates_x1"].update(0)
            window["click_coordinates_y1"].update(0)
            window["click_coordinates_x1"].update(disabled=True)
            window["click_coordinates_y1"].update(disabled=True)
        else:
            window["click_coordinates_x1"].update(disabled=False)
            window["click_coordinates_y1"].update(disabled=False)
        if x2 is None:
            window["click_coordinates_x2"].update(0)
            window["click_coordinates_y2"].update(0)
            window["click_coordinates_x2"].update(disabled=True)
            window["click_coordinates_y2"].update(disabled=True)
        else:
            window["click_coordinates_x2"].update(disabled=False)
            window["click_coordinates_y2"].update(disabled=False)
            
            
    def create_rectangles():
        for i in rectangle_numbers:
              window["canvas1"].delete_figure(i)
        rectangle_numbers.append(
            window["canvas1"].draw_rectangle(
                    top_left=(x1, y1),
                    bottom_right=(x2, y2),
                    line_color="red",
                    line_width=2))


    win_size = (750,750)
    pixels_amount = 560
    graph_size = (pixels_amount, int(pixels_amount * 3 / 4))
    col1 = [[sg.Text("mouse now:"), sg.Text("??", key="mouse_now", size=(20,1)), ],
        [sg.Text("last click: "), sg.Text("?,?",key="click_coordinates0"),  sg.Text("click #: 0", key="click_counter")]]
    col2 = [[sg.Text("1: topleft of r1, c1: ", key="c1", background_color="green"),
        sg.Spin(list(range(win_size[0])), key="click_coordinates_x1", enable_events=True),
        sg.Spin(list(range(win_size[1])), key="click_coordinates_y1", enable_events=True),],
        [sg.Text("2: bottomright r1, c1: ", key="c2"),
         sg.Spin(list(range(win_size[0])), key="click_coordinates_x2", enable_events=True),
         sg.Spin(list(range(win_size[1])), key="click_coordinates_y2", enable_events=True),]]
    mouse_column = [sg.Column(col1), sg.Column(col2)]
    
    layout = [[sg.Text("Patient: " + str(name)), 
               sg.Button("Next Channel", bind_return_key=True),
               sg.Button("Previous Channel", bind_return_key=True)],
              [mouse_column,],    
              [sg.Button("Crop with given coordinates"), sg.Button("Choose Whole Picture")],  
              [sg.Graph(canvas_size=graph_size,
                pad=0,
                graph_bottom_left=(0, graph_size[1]),
                graph_top_right=(graph_size[0], 0),
                key = "canvas1",
                enable_events=True,
                #motion_events=True,
                background_color= "#ccffcc",)],
             ]
    


    window = sg.Window(w_name,
                    layout = layout,
                    #size = win_size,
                    return_keyboard_events=True, 
                    grab_anywhere=True)
    
    
    original = None
    filename = None
    x,y = None, None
    x1,y1 = None, None
    x2,y2 = None, None
    Work_Book = {}
    canvas_x, canvas_y = 10, 206 # topleft of canvas 
    rectangle_numbers = []
    click_counter = 0

    window.finalize()

    window.bind('<Motion>', 'motion')
    ##### Showing image in the window 
    slice_of_hypercube = 1
    file = hypercube_of_images[:,:,1]
    uint8_file = np.uint8((file - file.min())/(file - file.min()).max()*255)
    image = Image.fromarray(uint8_file, mode = 'L') 
    image.thumbnail((graph_size[0], graph_size[1]))
    bio = io.BytesIO()
    image.save(bio, format="PNG")
    original = window["canvas1"].draw_image(data=bio.getvalue(), location = (0,0))
    #######
    while True:
        
        event,values = window.read()
        
        if event == sg.WINDOW_CLOSED:
            #window.close()
            #continue 
            break 
        
        

        if event == "canvas_x":
            canvas_x = int(values["canvas_x"])
        if event == "canvas_y":
            canvas_y = int(values["canvas_y"])

        if event == "motion":
            window["mouse_now"].update(motion())

        # get clicks coordinates
        if event == "canvas1":
            #print("clicked at:", values['canvas1'])
            window["click_coordinates0"].update(values['canvas1'])
            x,y = values['canvas1']
            click_counter += 1
            if click_counter > 2:
                click_counter = 0
            if click_counter == 0:
                x1,y1,x2,y2 = None, None, None, None
                update_spinners()
                window["c1"].update(background_color = "green")
                window["c2"].update(background_color = "grey")

                # delete all old rectangles
                for i in rectangle_numbers:
                    window["canvas1"].delete_figure(i)
            elif click_counter == 1:
                x1,y1 = x, y
                x2,y2 = None, None, 
                update_spinners()
                window["c1"].update(background_color = "grey")
                window["c2"].update(background_color = "green")

            elif click_counter == 2:
                x2, y2 = x, y
                update_spinners()
                window["c1"].update(background_color = "grey")
                window["c2"].update(background_color = "grey")
                #create_rectangles()
                for i in rectangle_numbers:
                    window["canvas1"].delete_figure(i)
                rectangle_numbers.append(
                    window["canvas1"].draw_rectangle(
                                top_left=(x1, y1),
                                bottom_right=(x2, y2),
                                line_color="red",
                                line_width=2))

            window["click_counter"].update(f"click #: {click_counter}")
            window["click_coordinates_x1"].update(value= x1)
            window["click_coordinates_y1"].update(value= y1)
            window["click_coordinates_x2"].update(value= x2)
            window["click_coordinates_y2"].update(value= y2)    

        if "click_coordinates_" in event:
            # a spinner was changed
            if x1 is not None:
                x1 = int(window["click_coordinates_x1"].get())
                y1 = int(window["click_coordinates_y1"].get())
            if x2 is not None:
                x2 = int(window["click_coordinates_x2"].get())
                y2 = int(window["click_coordinates_y2"].get())

            #print(x1,x2,x2,y2)
            for i in rectangle_numbers:
                window["canvas1"].delete_figure(i)
            rectangle_numbers.append(
                    window["canvas1"].draw_rectangle(
                                top_left=(x1, y1),
                                bottom_right=(x2, y2),
                                line_color="red",
                                line_width=2))
                #create_rectangles()

        if event == "Next Channel":
            if slice_of_hypercube == hypercube_of_images.shape[2]-1:
                if original is not None:
                    # delete old image first 
                    window["canvas1"].delete_figure(original)
                slice_of_hypercube += 0
                file = hypercube_of_images[:,:,slice_of_hypercube]
                uint8_file = np.uint8((file - file.min())/(file - file.min()).max()*255)
                image = Image.fromarray(uint8_file, mode = 'L') 
                image.thumbnail((graph_size[0], graph_size[1]))
                bio = io.BytesIO()
                image.save(bio, format="PNG")
                original = window["canvas1"].draw_image(data=bio.getvalue(), location = (0,0))
            else:
                if original is not None:
                    # delete old image first 
                    window["canvas1"].delete_figure(original)
                slice_of_hypercube += 1
                file = hypercube_of_images[:,:,slice_of_hypercube]
                uint8_file = np.uint8((file - file.min())/(file - file.min()).max()*255)
                image = Image.fromarray(uint8_file, mode = 'L') 
                image.thumbnail((graph_size[0], graph_size[1]))
                bio = io.BytesIO()
                image.save(bio, format="PNG")
                original = window["canvas1"].draw_image(data=bio.getvalue(), location = (0,0))
                
        if event == "Previous Channel":
            if slice_of_hypercube == 0:
                if original is not None:
                    # delete old image first 
                    window["canvas1"].delete_figure(original)
                slice_of_hypercube += 0
                file = hypercube_of_images[:,:,slice_of_hypercube]
                uint8_file = np.uint8((file - file.min())/(file - file.min()).max()*255)
                image = Image.fromarray(uint8_file, mode = 'L') 
                image.thumbnail((graph_size[0], graph_size[1]))
                bio = io.BytesIO()
                image.save(bio, format="PNG")
                original = window["canvas1"].draw_image(data=bio.getvalue(), location = (0,0))
            else:
                if original is not None:
                    # delete old image first 
                    window["canvas1"].delete_figure(original)
                slice_of_hypercube -= 1
                file = hypercube_of_images[:,:,slice_of_hypercube]
                uint8_file = np.uint8((file - file.min())/(file - file.min()).max()*255)
                image = Image.fromarray(uint8_file, mode = 'L') 
                image.thumbnail((graph_size[0], graph_size[1]))
                bio = io.BytesIO()
                image.save(bio, format="PNG")
                original = window["canvas1"].draw_image(data=bio.getvalue(), location = (0,0))

        if event == "Crop with given coordinates":
            window.close()
            
            Ref_adress = r'C:\Users\admin\Desktop\Skoltech\Project_Personal_medicine\Computational files\New Reference'
            for current_dir, next_dir, reference_files in os.walk(Ref_adress, topdown=True):
                continue

            for b in range(np.array(reference_files).size):
                if reference_files[b][::-1][4] != str(b+1):
                    print('Error in order of files')
                    break
                reference_files[b] = current_dir + '/' + reference_files[b]
                
            
            gray = lambda rgb : np.dot(rgb[... , :3] , [1. , 1., 1. ])
            ref_images_cube = np.array((gray(np.array(imageio.imread(reference_files[i]))) for i in range(8)))
#             ref_hypercube_of_images = np.dstack((tuple(ref_images_cube)))
        
        
            hc_output = hypercube_of_images[int(y1*2048/560):int(y2*2048/560),int(x1*2048/560):int(x2*2048/560),:]
            hc_output = hc_output / (ref_hypercube_of_images[int(y1*2048/560):int(y2*2048/560),int(x1*2048/560):int(x2*2048/560),:]+1e-3)
            
            return hc_output
        
        
        if event == "Choose Whole Picture":
            window.close()
            
            Ref_adress = r'C:\Users\admin\Desktop\Skoltech\Project_Personal_medicine\Computational files\New Reference'
            for current_dir, next_dir, reference_files in os.walk(Ref_adress, topdown=True):
                continue

            for b in range(np.array(reference_files).size):
                if reference_files[b][::-1][4] != str(b+1):
                    print('Error in order of files')
                    break
                reference_files[b] = current_dir + '/' + reference_files[b]
                
                
            ref_images_cube = (np.array(imageio.imread(reference_files[i])) for i in range(8))
            ref_hypercube_of_images = np.dstack((tuple(ref_images_cube)))
        
        
            hc_output = hypercube_of_images
            hc_output = hc_output / (ref_hypercube_of_images+1e-3)
            
            return hc_output
        
    window.close()
    return Work_Book


# In[4]:


def PCA_ICA(names, number_of_components, if_use_ICA = True):
    hypercube_of_images = {}
    for i in names:
        hypercube_of_images[i] = crop_image(upload(i), i)
        
    width = hypercube_of_images[names[0]].shape[0]
    height = hypercube_of_images[names[0]].shape[1]
    channels = hypercube_of_images[names[0]].shape[2]
    image = np.reshape(hypercube_of_images[names[0]], (width*height, channels))
    
    df = pd.DataFrame(image)
    PCA_transformer = sklearnPCA(n_components=number_of_components, svd_solver='arpack') 
    # Has to be arpack or fixed random number for results to be reproducable between different trials
    # X_std = StandardScaler().fit_transform(df) Values already normalized in 8bit because of the camera [0:255]
    # Y_sklearn = sklearn_pca.fit_transform(X_std)
    PCA_transformed_hypercube = PCA_transformer.fit_transform(df)
    output = {}
    print('Explained_variance_ratio_by_each_component = ', PCA_transformer.explained_variance_ratio_)
    print('Explained_variance_ratio = ', np.sum(PCA_transformer.explained_variance_ratio_))
    
    if if_use_ICA:
        ICA_transformer = FastICA(n_components=number_of_components, random_state=1) 
        # Random_state has to be fixed for results to be reproducable between different trials
        ICA_PCA_transformed_hypercube = ICA_transformer.fit_transform(PCA_transformed_hypercube)
        y_df = pd.DataFrame(ICA_PCA_transformed_hypercube)
        output[names[0]] = np.array(y_df).reshape((width,height,number_of_components))
        
        for i in names[1:]:
            width = hypercube_of_images[i].shape[0]
            height = hypercube_of_images[i].shape[1]
            image = np.reshape(hypercube_of_images[i], (width*height, channels))
            df = pd.DataFrame(image)
            PCA_transformed_hypercube = PCA_transformer.transform(df)
            ICA_PCA_transformed_hypercube = ICA_transformer.transform(PCA_transformed_hypercube)
            y_df = pd.DataFrame(ICA_PCA_transformed_hypercube)
            output[i] = np.array(y_df).reshape((width,height,number_of_components))
        return output
      
    else:
        y_df = pd.DataFrame(PCA_transformed_hypercube)
        output[names[0]] = np.array(y_df).reshape((width,height,number_of_components))
        for i in names[1:]:
            width = hypercube_of_images[i].shape[0]
            height = hypercube_of_images[i].shape[1]
            image = np.reshape(hypercube_of_images[i], (width*height, channels))
            df = pd.DataFrame(image)
            PCA_transformed_hypercube = PCA_transformer.fit_transform(df)
            y_df = pd.DataFrame(PCA_transformed_hypercube)
            output[i] = np.array(y_df).reshape((width,height,number_of_components))
            print('Explained_variance_ratio_by_each_component = ', PCA_transformer.explained_variance_ratio_)
            print('Explained_variance_ratio = ', np.sum(PCA_transformer.explained_variance_ratio_))

        return output


# In[5]:


def Segmentation_Otsu(dictionary_of_visits, name, which_component_to_use, gaussian_blur):
    
    to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
    uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
    blured_area = gaussian(to_fit_area, gaussian_blur)
    min_value = blured_area.min()
    max_value = blured_area.max()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # treshold_in_real_map = ret*(max_value - min_value)/255 + min_value
#     contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
# #     area_list = []
# #     for cnt in contours:
# #         area_list.append(cv2.contourArea(cnt))
# #     contour = contours[np.array(area_list).argmax()] 
#     #We are interested in only highest area contour 
    
#     image_with_contours = cv2.drawContours(uint8_to_fit_area, contours, -1, (255, 0, 255), 5)
#     plt.imshow(image_with_contours)
#     plt.xticks(ticks = [])
#     plt.yticks(ticks = [])
#     plt.show()
    
    
# #     mask = np.zeros(to_fit_area.shape, np.uint8)
# #     cv2.drawContours(mask, [contour], 0, 255, -1)
# #     cv2.drawContours(mask, [contours], 0, 255, -1)
    
#     plt.imshow(th*to_fit_area)
#     plt.xticks(ticks = [])
#     plt.yticks(ticks = [])
#     plt.show()

   
    return th
#There is a need to add mask as determined by all contours
#Also by hands choice of contour, something like: "please pick # of a contour"


# In[6]:


def analysis_of_distributions(dictionary_of_visits, names, which_component_to_use, gaussian_blur):
    mean_array = {'hemangioma':{}, 'skin': {}}
    std_array = {'hemangioma':{}, 'skin': {}}
    contour_data_for_stat = {}
    dataframe_for_stat = pd.DataFrame(contour_data_for_stat)
    
    for name in names:
        mask = Segmentation_Otsu(dictionary_of_visits = dictionary_of_visits, name = name, which_component_to_use = which_component_to_use, gaussian_blur = gaussian_blur)
        
        to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
        uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)

        X = np.ravel(mask * to_fit_area)/255
#         plt.imshow(uint8_to_fit_area)
#         plt.colorbar()
#         plt.show()
        
#         plt.imshow(mask)
#         plt.colorbar()
#         plt.show()
        
#         plt.imshow(mask * uint8_to_fit_area)
#         plt.colorbar()
#         plt.show()
        
#         plt.imshow(mask*to_fit_area)
#         plt.colorbar()
#         plt.show()
        
        
        #values_hemangioma = [i for i in X if i!=0]
        values_hemangioma = np.array((np.array([i for i in X if i!=0]) - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255)
        
        X = np.ravel((255 - mask) * to_fit_area)/255
        values_skin = np.array((np.array([i for i in X if i!=0]) - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255)
        

        mean_array['skin'][name] = np.mean(values_skin)
        std_array['skin'][name] = np.std(values_skin)
        

        mean_array['hemangioma'][name] = np.mean(values_hemangioma)
        std_array['hemangioma'][name] = np.std(values_hemangioma)
        
    return mean_array, std_array


# In[7]:


def align_yaxis(ax1, ax2):
    y_lims = np.array([ax.get_ylim() for ax in [ax1, ax2]])

    # force 0 to appear on both axes, comment if don't need
    y_lims[:, 0] = y_lims[:, 0].clip(None, 0)
    y_lims[:, 1] = y_lims[:, 1].clip(0, None)

    # normalize both axes
    y_mags = (y_lims[:,1] - y_lims[:,0]).reshape(len(y_lims),1)
    y_lims_normalized = y_lims / y_mags

    # find combined range
    y_new_lims_normalized = np.array([np.min(y_lims_normalized), np.max(y_lims_normalized)])

    # denormalize combined range to get new axes
    new_lim1, new_lim2 = y_new_lims_normalized * y_mags
    ax1.set_ylim(new_lim1)
    ax2.set_ylim(new_lim2)

    
    
def Offset_Percentage_Adjustment(dictionary_of_visits, name, which_component_to_use, gaussian_blur, offset_percent_1, offset_percent_2):
    
    to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
    uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
    blured_area = gaussian(to_fit_area, gaussian_blur)
    min_value = blured_area.min()
    max_value = blured_area.max()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # treshold_in_real_map = ret*(max_value - min_value)/255 + min_value
    contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    area_list = []
    for cnt in contours:
        area_list.append(cv2.contourArea(cnt))
    contour = contours[np.array(area_list).argmax()] 
    #We are interested in only highest area contour 
    
    start = ret*(1-offset_percent_1/100)
    stop = ret*(1+offset_percent_2/100)
    
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    th1, binary = cv2.threshold(treated_area, start, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(np.uint8(255*binary), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    image = cv2.drawContours(treated_area, contours, -1, (255, 0, 255), 5)
    plt.imshow(image)
    plt.show()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    th2, binary = cv2.threshold(treated_area, stop, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(np.uint8(255*binary), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    image = cv2.drawContours(treated_area, contours, -1, (255, 0, 255), 5)
    plt.imshow(image)
    plt.show()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    return ret, th1, th2
    
    
    
    
def Borders_values(dictionary_of_visits, name, which_component_to_use, gaussian_blur, step = 1):#, show_pic = False):
    
    to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
#     uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
    blured_area = gaussian(to_fit_area, gaussian_blur)
    min_value = blured_area.min()
    max_value = blured_area.max()
#     treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
#     start = ret*(1-offset_percent_1/100)
#     stop = max_value#ret*(1+offset_percent_2/100)
    stop = 255
    mean, std, area, length = line_array(treated_area, ret, stop, step)
       
    return mean, std, area, length



def contours(treated_area, tr_start, tr_end):#, show_pic = False):
        
    _, binary = cv2.threshold(treated_area, tr_start, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(np.uint8(255*binary), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    area_ar = [cv2.contourArea(cnt) for cnt in contours]
            
    if area_ar == []:
        contour_area = 0
    else:
        contour_area = sum(area_ar)     
        
    #     contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
#     area_list = []
#     for cnt in contours:
#         area_list.append(cv2.contourArea(cnt))
#     contour = contours[np.array(area_list).argmax()] 
    #We are interested in only highest area contour 

    _, binary2 = cv2.threshold(treated_area, tr_end, 255, cv2.THRESH_BINARY)
    
#     if show_pic:
#         contours, hierarchy = cv2.findContours(np.uint8(255*(binary-binary2)), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#         image2 = cv2.drawContours(np.uint8(treated_area), contours, -1, (255, 0, 255), 5)
#         plt.imshow(image2)
#         plt.show()
#         plt.imshow((binary-binary2)*treated_area)
#         plt.show()
    
    X = np.ravel((binary2-binary)*treated_area)
    X = [i for i in X if i!=0]
    return (np.mean(X), np.std(X), contour_area, len(X))

def line_array(treated_area, start, stop, step = 1):#, show_pic = False):
                  
    mean = []
    std = []
    area = []
    length = []
    for i in tqdm(np.arange(start, stop, step)):
        m, s, a, l = contours(treated_area, i, i+step)
        
        if (np.isnan(m) or np.isnan(s)):
            mean.append(mean[-1])
            std.append(std[-1])
            area.append(area[-1])
            length.append(length[-1])
        else:
            mean.append(m)
            std.append(s)
            area.append(a)
            length.append(l)
            
    return mean, std, area, length


def Full_Image_Borders_values(dictionary_of_visits, name, which_component_to_use, gaussian_blur, step = 1, show_pic = False):
    
    to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
    uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
    blured_area = gaussian(to_fit_area, gaussian_blur)
    min_value = blured_area.min()
    max_value = blured_area.max()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    mean, std, area, length = Full_Image_line_array(treated_area, start = 0, stop = 255, step = 1, show_pic = False)
       
    return mean, std, area, length



def Full_Image_contours(treated_area, tr_start, tr_end, show_pic = False):
        
    _, binary = cv2.threshold(treated_area, tr_start, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(np.uint8(255*binary), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    area_ar = [cv2.contourArea(cnt) for cnt in contours]
            
    if area_ar == []:
        contour_area = 0
    else:
        contour_area = max(area_ar)     
        
    #     contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
#     area_list = []
#     for cnt in contours:
#         area_list.append(cv2.contourArea(cnt))
#     contour = contours[np.array(area_list).argmax()] 
    #We are interested in only highest area contour 

    _, binary2 = cv2.threshold(treated_area, tr_end, 255, cv2.THRESH_BINARY)
    
    if show_pic:
        contours, hierarchy = cv2.findContours(np.uint8(255*(binary-binary2)), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        image2 = cv2.drawContours(np.uint8(treated_area), contours, -1, (255, 0, 255), 5)
        plt.imshow(image2)
        plt.show()
        plt.imshow((binary-binary2)*treated_area)
        plt.show()
    
    X = np.ravel((binary2-binary)*treated_area)
    X = [i for i in X if i!=0]
    return (np.mean(X), np.std(X), contour_area, len(X))

def Full_Image_line_array(treated_area, start, stop, step = 1, show_pic = False):
                  
    mean = []
    std = []
    area = []
    length = []
    for i in tqdm(np.arange(start, stop, step)):
        m, s, a, l = Full_Image_contours(treated_area, i, i+step, show_pic)
        
        if (np.isnan(m) or np.isnan(s)):
            mean.append(mean[-1])
            std.append(std[-1])
            area.append(area[-1])
            length.append(length[-1])
        else:
            mean.append(m)
            std.append(s)
            area.append(a)
            length.append(l)
            
    return mean, std, area, length

def print_borders_thresholds(dictionary_of_visits, name, which_component_to_use, gaussian_blur, offset_percent_1, offset_percent_2, step = 1, show_pic = False):
    
    to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
    uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
    blured_area = gaussian(to_fit_area, gaussian_blur)
    min_value = blured_area.min()
    max_value = blured_area.max()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    start = ret*(1-offset_percent_1/100)
    stop = ret*(1+offset_percent_2/100)
       
    return start, stop, ret


def extract_skin_value(dictionary_of_visits, name, which_component_to_use, gaussian_blur):
    
    to_fit_area = dictionary_of_visits[name][:,:,which_component_to_use]
    uint8_to_fit_area = np.array((to_fit_area - to_fit_area.min())/(to_fit_area.max() - to_fit_area.min())*255, dtype = np.uint8)
    blured_area = gaussian(to_fit_area, gaussian_blur)
    min_value = blured_area.min()
    max_value = blured_area.max()
    treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
    
    ret, th = cv2.threshold(treated_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # treshold_in_real_map = ret*(max_value - min_value)/255 + min_value
    contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
      
#     start = ret*(1-offset_percent_1/100)
    
#     treated_area = np.array((blured_area - min_value)/(max_value - min_value)*255, dtype = np.uint8)
#     th1, binary = cv2.threshold(treated_area, start, 255, cv2.THRESH_BINARY)
#     contours, hierarchy = cv2.findContours(np.uint8(255*binary), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     image = cv2.drawContours(treated_area, contours, -1, (255, 0, 255), 5)
#     plt.imshow(image)
#     plt.show()
#     new_b = np.array(1 - binary/255)
    new_b = 1 - th#morphology.isotropic_dilation(th, radius = 45)
#     plt.imshow(np.array(binary/255))
#     plt.show()


#     plt.imshow(new_b * treated_area)
#     plt.colorbar()
#     plt.show()
    
    X = np.ravel(new_b * treated_area)
    X = [i for i in X if i!=0]
    return np.mean(X)