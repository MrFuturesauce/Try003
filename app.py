##  Status --- Works as-is.  AE table with 3 selectors

#%%
import pandas as pd


from shiny import reactive
from shiny.express import input, render, ui
from shiny.types import FileInfo
from functools import partial
from shiny.ui import page_navbar
# from great_tables import gt
import matplotlib.pyplot as plt
#%%

# path = r'C:\Users\BrianConley\OneDrive - SFJ Pharmaceuticals\WORK\Python\sdtm-adam-pilot-project-master\updated-pilot-submission-package\900172\m5\datasets\cdiscpilot01\analysis\adam\datasets\adae.xpt'
path = r'.\Data\adae.xpt'

adae = pd.read_sas(path, encoding = 'utf8')

# pathadsl = r"C:\Users\BrianConley\OneDrive - SFJ Pharmaceuticals\WORK\Python\sdtm-adam-pilot-project-master\updated-pilot-submission-package\900172\m5\datasets\cdiscpilot01\analysis\adam\datasets\adsl.xpt"

pathadsl = r".\Data\adsl.xpt"

adsl = pd.read_sas(pathadsl, encoding = 'latin1')

sex = list(adsl["SEX"].value_counts().index)


# pathlabc = r"C:\Users\BrianConley\OneDrive - SFJ Pharmaceuticals\WORK\Python\sdtm-adam-pilot-project-master\updated-pilot-submission-package\900172\m5\datasets\cdiscpilot01\analysis\adam\datasets\adlbc.xpt"
pathlabc = r".\Data\adlbc.xpt"
adlbc = pd.read_sas(pathlabc, encoding = 'utf8').round({'AVISITN': 0, 'TRTAN': 0, 'TRTPN': 0})


mapping_dict = {'Placebo': 0, 'Xanomeline Low Dose': 1, 'Xanomeline High Dose': 2}

# @reactive.Calc
def get_age_min():
    # maxage = adsl["AGE"].max()
    minage = adsl["AGE"].min()
    return minage

# @reactive.Calc
def get_age_max():
    maxage = adsl["AGE"].max()    
    return maxage
    
    
# Get the ADAE data, subsetting for Sex
@reactive.calc
def get_alltrts():
    # adae2 = adae[adae["SEX"].isin(input.Sex())]
    AEs = []
    sex = input.Sex()
    agelow = input.age()[0]
    agehi = input.age()[1]
    if input.SER() == True:
        AEs = ['Y']
    else:
        AEs = ['Y', 'N', ' ']
    adae2 = (adae.query("SEX in @sex")
                 .query("AGE >=@agelow")
                 .query("AGE <=@agehi")
                 .query("AESER in @AEs")
        
    )
    
    # adae3 = adae2[adae2["AGE"].between(input.age())]
    print(input.age()[1])
    print(f"Sex is {input.Sex()}")
    
    # make a dataset with trts and overall rows
    
    alltrts = pd.concat([adae2.query("TRTEMFL == 'Y' ").assign(trt = lambda x: x['TRTA'].map(mapping_dict)) ,                    
                        (adae2.query("TRTEMFL == 'Y' ").assign(trt = 3))       
                
            ])
    
    return alltrts
    
#Get the ADSL data, subsetting for Sex

@reactive.calc
def get_alladsl():    
    # adsl2 = adsl[adsl["SEX"].isin(input.Sex())]
    
    sex = input.Sex()
    agelow = input.age()[0]
    agehi = input.age()[1]
    adsl2 = (adsl.query("SEX in @sex")
                 .query("AGE >=@agelow")
                 .query("AGE <=@agehi")
        
    )    
    allADSL = pd.concat([adsl2.query("SAFFL == 'Y'").assign(trt = lambda x: x['ARM'].map(mapping_dict)) ,                    
                            (adsl2.query("SAFFL == 'Y'").assign(trt = 3))       
                    
                ])
    ADSLtrts = allADSL[['SUBJID', 'trt']]

    # column Ns
    totpop = allADSL.query("SAFFL == 'Y'").value_counts(subset=['trt'])
    return ADSLtrts, totpop

@reactive.calc
def get_SOC():
    
    def bccount2(col):
        adsltrts, totpop = get_alladsl()
        ucnt = col.nunique()
        cnt = col.count()
        # perc = (ucnt / total(adsl)) * 100
        #st = f"{ucnt}  ({(ucnt / total(alltrts)) * 100:.1f}%)    [{cnt}]"
        st = f"{ucnt}  ({(ucnt / totpop[trt]) * 100:.1f}%)    [{cnt}]"
        
        return st
    
    cols = ('Placebo', 'Xanomeline Low Dose', 'Xanomeline High Dose', 'Total')
    alltrts = get_alltrts()

    dfs = []
    trts = (0, 1, 2, 3)
    for trt in trts:
        data =   (
                        alltrts.query("TRTEMFL == 'Y' and trt == @trt")                    
                        .groupby(["AESOC"])['USUBJID']
                        .agg([bccount2])
                        .assign(ord = 1, AEDECOD = ' ', col = trt)
                        .reset_index()                    
                        
                        .rename(columns={"bccount2": cols[trt]})
                        .drop(["col"], axis = 1)
                        # .set_index(["AESOC", "AEDECOD", "ord"])
                        # .assign(ord = 1)
            )
        dfs.append(data)
        

    SOCmerge = dfs[0]
    for df in dfs[1:]:
        SOCmerge = pd.merge(SOCmerge, df, on = ["AESOC", "AEDECOD", "ord"], how = 'outer')
        
    # return SOCmerge
    dfs = []
    trts = (0, 1, 2, 3)
    for trt in trts:
        data =   (
                        alltrts.query("TRTEMFL == 'Y' and trt == @trt")                    
                        .groupby(["AESOC", 'AEDECOD'])['USUBJID']
                        .agg([bccount2])
                        .assign(ord = 2, col = trt)
                        .reset_index()
                        .rename(columns={"bccount2": cols[trt]})
                        .drop(["col"], axis = 1)
                        # .set_index(["AESOC", "AEDECOD", "ord"])
                        # .assign(ord = 1)
            )
        dfs.append(data)            
        

    DECODmerge = dfs[0]
    for df in dfs[1:]:
        DECODmerge = pd.merge(DECODmerge, df, on = ["AESOC", "AEDECOD", "ord"], how = 'outer')
        
    # return DECODmerge

    AERpt = pd.concat([SOCmerge, DECODmerge]).sort_values(by=["AESOC", "AEDECOD", 'ord'])


# %%
    def colcomb(x):
        if x.ord == 1:
            coltxt = x.AESOC
            
        if x.ord == 2:
            coltxt = "" + x.AEDECOD
            
        return coltxt


    AEFinal = (AERpt.assign(coltxt = lambda x: x.apply(colcomb, axis = 1)) ## use of assign and custom function,
                    .reset_index()
                    .get([ 'coltxt', 'Placebo', 'Xanomeline Low Dose', 'Xanomeline High Dose', 'Total', 'ord'])
                    .rename(columns={'coltxt' : 'SOC/ Preferred Term'})
                    
                    
                    
        
    )    
    
    # AEFinal.set_index('coltxt')
    indrow = []
    indrow = AEFinal[AEFinal['ord'] == 2].index.to_list()
    print(indrow)
    
    ## get rid of the ord variable
    AEFinal = (AEFinal.get([ 'SOC/ Preferred Term', 'Placebo', 'Xanomeline Low Dose', 'Xanomeline High Dose', 'Total'])                                                               
        
    ) 
    
    hi_styles = [
    
    {
        
        "cols": [0],
        "class": "posit-blue-bg",
        "style": {
            "width": "900px"
        },
    },
    {
        
        "cols": [1, 2, 3, 4],
        "class": "posit-blue-bg",
        "style": {
            "width": "200px"
        },
    },
    
    {"rows": indrow,
     "cols": [0],
     "style": {"text-indent": "30px"}
    }
]
    
    print(hi_styles)
    return AEFinal, hi_styles
###############################################################################################
#  Lab data section #

###############################################################################################

@reactive.calc
def get_labc():
    # adae2 = adae[adae["SEX"].isin(input.Sex())]
    
    # sex = input.Sexlab()
    # agelow = input.agelab()[0]
    # agehi = input.agelab()[1]
    slab = input.selectlab()
    plist = input.selectlabparam()
    adlbc2 = (adlbc.query("USUBJID == @slab")
                   .query("PARAM == @plist")
                 
        
    )
    return adlbc2
    

def getlablist():
    labclist = []
    labclist = (adlbc['USUBJID'].unique().tolist())
    
    print(labclist)
    return labclist

def getlablistparam():
    labclistparam = []
    labclistparam = (adlbc['PARAM'].unique().tolist())
    
    return labclistparam

###############################################################################################
#  Page layout section #
###############################################################################################
####################

ui.tags.style(
    ui.HTML(
        """
    .posit-bg {
        background-color: #242a26 ;
    }
    .posit-blue-bg {
        background-color: #447099 ;
    }
    .posit-orange-bg {
        background-color: #ED642F ;
    }
    """
    )
)

# indrow = [1, 2, 3, 4, 5]




###################

ui.page_opts(fillable=True)


# rowlist = get_SOC()[1]
with ui.navset_tab(id="Top_Level"):
    with ui.nav_panel("Adverse Event"):    

        with ui.layout_sidebar():
            with ui.sidebar(id="sidebar_left", open="desktop"):
                    ui.input_checkbox_group(
                    "Sex", "Sex:",
                    sex, selected = sex
                    )   
                    ui.input_slider("age", "Choose Age", step = 1, min=get_age_min(), max=get_age_max(), value=[get_age_min(), get_age_max()]) 
                    ui.input_checkbox("SER", "Serious AEs Only", False)  
                    
            with ui.navset_tab(id="selected_navset_tab"):
                
                with ui.nav_panel("Adverse Event Data"):
                    @render.data_frame  
                    def penguins_df():    
                        return render.DataGrid(get_alltrts(), filters=False)  
                    
                with ui.nav_panel("AE Counts by System Organ Class and Preferred Term"):
                    @render.ui
                    def rows():
                        rows = soc_df.data_view(selected=True)  # <<
                        selected = ", ".join(str(i) for i in sorted(rows.index)) if not rows.empty else "None"
                        return f"Rows selected: {selected}"
                    @render.data_frame  
                    def soc_df():    
                        rowlist = get_SOC()[1]
                        # print(rowlist.describe())
                        return render.DataTable(get_SOC()[0], filters=False , styles=rowlist, selection_mode = 'row') 
                        # return render.DataTable(get_SOC()[0], filters=False )    
    #######################################################
    
    with ui.nav_panel("Laboratory Data"):   
         
         
        with ui.card(): ##Top card, holding selectors and graph
            with ui.layout_sidebar():
                with ui.sidebar(id="sidebar_lab", open="desktop"):
                        
                        ui.input_select(  
                                        "selectlab",  
                                        "Select USUBJID for graph:",  
                                        getlablist(),  
                                        )  
                        
                        ui.input_select(  
                                        "selectlabparam",  
                                        "Select Lab Parameter for graph:",  
                                        getlablistparam(),  
                                        )  
                @render.plot(alt="A histogram")  # <<
                def plot():  # <<
                    df = (get_labc().query("AVISITN < 99"))
                    x = df['AVISIT']
                    y = df['AVAL']

                    fig, ax = plt.subplots()
                    # ax.hist(mass, input.n(), density=True)
                    ax.plot(x, y, marker = 'o')
                    ax.set_title(f"Results of {input.selectlabparam()} for USUBJID = {input.selectlab()}")
                    ax.set_ylabel(f"{input.selectlabparam()}")
                    ax.set_xlabel("Visit")

                    return fig  # <<
    
        with ui.card(): ## Bottom card, holding data                       
            with ui.navset_tab(id="selected_lab_tab"):                    
                with ui.nav_panel("Lab Data"):
                    @render.data_frame  
                    def labtab():    
                                        
                        return render.DataTable(get_labc(), filters=False ) 
                                                    

