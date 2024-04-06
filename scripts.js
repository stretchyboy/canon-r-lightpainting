const form = document.querySelector("#frameselect");
const frame = document.querySelector("#frame");
const submit = document.querySelector("#submit");
const feedback = document.querySelector("#feedback");
const sightingdots = document.querySelector("#sightingdots");
const body = document.querySelector("body");
var loaded = ""
var bConnected = false

const increment = document.querySelector("#increment");
const decrement = document.querySelector("#decrement");


function addFeedback(text){
  feedback.innerHTML = text+"\n"+feedback.innerHTML 
}

async function sendData() {
  // Associate the FormData object with the form element
  const formData = new FormData(form);
  console.log("formData", formData)
  if (loaded == ""){
    addFeedback("Loading")
    try {
        const response = await fetch("/load/"+formData.get("cat")+"/anim/"+formData.get("anim")+"/"+formData.get("frame"), {
        method: "GET",
        cache:"no-store",
        // Set the FormData instance as the request body
        /*headers: {
          "Content-Type": "application/json",
          // 'Content-Type': 'application/x-www-form-urlencoded',
          
        },*/
        });
        
        const stickframe = await response.text();
        console.log("stickframe", stickframe)
        addFeedback("Loaded")//\nImage is "+stickframe.widthCM+"cm wide")
        submit.setAttribute("value", "Show")
        loaded = formData.get("frame")
    } catch (e) { 
        unload("Load Failed")
    }
  } else { 
    sightingdots.checked = false
    addFeedback("Showing")
    await sendShutter()
    
    //body.style.backgroundColor = "black";
    try {    
        const response = await fetch("/show/"+formData.get("cat")+"/anim/"+formData.get("anim")+"/"+formData.get("frame")+"/"+formData.get("duration"), {
        method: "GET",
        cache:"no-store",
        // Set the FormData instance as the request body
        });
        const showdata = await response.text();
        if(response.status == 200)
        {
          addFeedback("Shown")
        }
        else
        {
          addFeedback("Not Shown")
        }
        await sendShutter("release")
        body.style.backgroundColor = "white";
    } catch (e) {
        await sendShutter("release")
        addFeedback("Show Failed")
        console.error(e);
    }

        
  }
}

function unload(msg=""){
    addFeedback(msg)
    loaded = ""
    submit.setAttribute("value", "Load")
    body.style.backgroundColor = "white";
}

async function sendConnect() {
  // Associate the FormData object with the form element
  try {
        const response = await fetch(CAMERAURL, {
        method: "GET",
        mode:    "no-cors",
        cache:"no-store",
        // Set the FormData instance as the request body
        });
        addFeedback("Camera Connected")
        bConnected = true
    } catch (e) {
        bConnected = false
        addFeedback("Camera Connect failed")
        console.error(e);
    }
}

async function sendSightingDots(on) {
  // Associate the FormData object with the form element
  //console.log("sendSightingDots", on)
  try {
        const response = await fetch("/sightingdots/"+on, {
        cache:"no-store",
         method: "GET",
        // Set the FormData instance as the request body
        });
        status = "off"
        if(on){
            status = "on"
        }
        addFeedback("Sighting Dots "+status)

    } catch (e) {
        addFeedback("Sighting Dots changed failed")
        console.error(e);
    }
}

async function sendShutter(action="full_press") { // ["full_press", "half_press", "release"]:
  if (bConnected == false){
    return
  }
  // Associate the FormData object with the form element
  try {
    addFeedback("Shutter "+action)
    const data = {"af": false,
                        "action": action
                    }

        const response = await fetch(CAMERAURL+"/ver100/shooting/control/shutterbutton/manual", {
        mode:    "no-cors",
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                // 'Content-Type': 'application/x-www-form-urlencoded',
                
              },
              redirect: "follow", // manual, *follow, error
              referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
              body: JSON.stringify(data), 
        });
        addFeedback("Shutter "+action+" done")
    } catch (e) {
        addFeedback("Shutter "+action +" possible")
        console.error(e);
    }
}

document.addEventListener("DOMContentLoaded", (event) => {
  console.log("DOMContentLoaded", event)
  sendConnect();
  sendData();
});


form.addEventListener("submit", (event) => {
  event.preventDefault();  
  console.log("sendData")
  sendData();
});

sightingdots.addEventListener("change", (event) => {
  on = 0
  if (sightingdots.checked == true){
    on = 1
  }
  //console.log("sightingdots", event, on)
  sendSightingDots(on);
});

frame.addEventListener("change", (event) => {
  unload()
})

increment.addEventListener("click", (event) => {
    event.preventDefault();
    console.log("frame", frame)
    unload("Next Frame will need to be loaded")
    frame.stepUp();
})

decrement.addEventListener("click", (event) => {
    event.preventDefault();
    unload("Previous Frame will need to be loaded")
    frame.stepDown();
})
