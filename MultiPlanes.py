from .lib import fusionAddInUtils as futil
import adsk.core
import os
import adsk.fusion
import traceback
#from . import config
app = adsk.core.Application.get()
ui = app.userInterface
# TODO *** Specify the command identity information. ***
CMD_ID = "Multi_Planes"
CMD_NAME = 'Multi Planes'
CMD_Description = '' #Add a description of the add-in
IS_PROMOTED = True
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'ConstructionPanel'
COMMAND_BESIDE_ID = 'WorkPlaneFromPointAndNormalCommand'
PlaneQTY = 5
DistValue = 5
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')


local_handlers = []
def run(context):
    try:
        cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
        futil.add_handler(cmd_def.commandCreated, command_created)
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
        control.isPromoted = IS_PROMOTED
        #start()

    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        command_control = panel.controls.itemById(CMD_ID)
        command_definition = ui.commandDefinitions.itemById(CMD_ID)

        if command_control:
            command_control.deleteMe()

        if command_definition:
            command_definition.deleteMe()


    except:
        futil.handle_error('stop')



def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    BasePlane = inputs.addSelectionInput("BasePlane", "Base Plane", "Select a Planar entity")
    BasePlane.addSelectionFilter("PlanarFaces") #https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-03033DE6-AD8E-46B3-B4E6-DADA8D389E4E
    BasePlane.addSelectionFilter("ConstructionPlanes")
    planeqty = inputs.addIntegerSpinnerCommandInput("PlaneQTY", "Number of Planes", 1, 100, 1, PlaneQTY)
    Distance = inputs.addDistanceValueCommandInput("Value", "Value", adsk.core.ValueInput.createByReal(DistValue))
    Distance.isEnabled = False
    Distance.isVisible = False
    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    BasePlaneSelecter: adsk.core.SelectionCommandInput = inputs.itemById("BasePlane")
    planeqty: adsk.core.IntegerSpinnerCommandInput = inputs.itemById("PlaneQTY")
    Value: adsk.core.ValueCommandInput = inputs.itemById("Value")
    Worker(BasePlaneSelecter.selection(0).entity, planeqty.value, Value.value)
    global PlaneQTY
    global DistValue
    PlaneQTY = planeqty.value
    DistValue = Value.value


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    BasePlaneSelecter: adsk.core.SelectionCommandInput = inputs.itemById("BasePlane")
    planeqty: adsk.core.IntegerSpinnerCommandInput = inputs.itemById("PlaneQTY")
    Value: adsk.core.ValueCommandInput = inputs.itemById("Value")
    Worker(BasePlaneSelecter.selection(0).entity, planeqty.value, Value.value)


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs
    selection_input: adsk.core.SelectionCommandInput = inputs.itemById('BasePlane')
    distance_input: adsk.core.DistanceValueCommandInput = inputs.itemById('Value')
    if changed_input.id == selection_input.id:
        if selection_input.selectionCount > 0:
            selection = selection_input.selection(0)
            selection_point = selection.point
            selected_entity = selection.entity
            plane = selected_entity.geometry

            distance_input.setManipulator(selection_point, plane.normal)
            distance_input.expression = "10mm * 2"
            distance_input.isEnabled = True
            distance_input.isVisible = True
    # General logging for debug.
    #futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    #futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.

        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []

def Worker(Plane, Qty, Distance):

    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design: adsk.fusion.Design = app.activeProduct
        rootComp: adsk.fusion.Component = design.rootComponent

        # Define the number of planes and the distance between them
        num_planes = Qty
        distance = Distance # Distance in cm

        # Get the base plane (XY plane in this case)
        base_plane = Plane

        for i in range(num_planes):
            offset_value = adsk.core.ValueInput.createByReal(distance * (i + 1))
            PlaneInput = rootComp.constructionPlanes.createInput()
            PlaneInput.setByOffset(base_plane, offset_value)
            offset_plane = rootComp.constructionPlanes.add(PlaneInput)
            offset_plane.name = f'Offset Plane {i + 1}'

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
