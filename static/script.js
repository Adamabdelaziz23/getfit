const menuBtn = document.querySelector('.menu-btn');
const dropdownMenu = document.getElementById('dropdownmenu');

document.addEventListener("DOMContentLoaded", function() {
    const menuBtn = document.querySelector(".menu-btn");
    const dropdownMenu = document.getElementById("dropdownmenu");

    if (menuBtn && dropdownMenu) {
        // Hide menu by default on load
        dropdownMenu.style.display = "none";

        // Toggle menu display on click
        menuBtn.addEventListener("click", function(event) {
            event.stopPropagation();
            if (dropdownMenu.style.display === "none" || dropdownMenu.style.display === "") {
                dropdownMenu.style.display = "block";
            } else {
                dropdownMenu.style.display = "none";
            }
        });

        // Close menu when clicking anywhere else on the page
        document.addEventListener("click", function(event) {
            if (!dropdownMenu.contains(event.target) && !menuBtn.contains(event.target)) {
                dropdownMenu.style.display = "none";
            }
        });
    }
});


// Calorie Calculator Logic
const calcForm = document.getElementById('calcForm');
if (calcForm) {
    calcForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const age = parseInt(document.getElementById('age').value);
        const gender = document.getElementById('gender').value;
        const weight = parseFloat(document.getElementById('weight').value);
        const height = parseFloat(document.getElementById('height').value);
        // BMR Calculation
        let bmr = (10 * weight) + (6.25 * height) - (5 * age);
        bmr += (gender === 'male') ? 5 : -161;
        // Estimated maintenance calories (light activity factor ~1.375)
        const totalCalories = Math.round(bmr * 1.375);
        const resultDiv = document.getElementById('calcResult');
        resultDiv.style.display = 'block';
        resultDiv.innerText =
            `Your Estimated Maintenance Calories: ${totalCalories} kcal/day`;
    });
}
// Rest Timer Logic
let timerInterval = null;

function startTimer(seconds) {
    clearInterval(timerInterval);
    let remainingTime = seconds;
    updateTimerDisplay(remainingTime);
    timerInterval = setInterval(() => {
        remainingTime--;
        updateTimerDisplay(remainingTime);
        if (remainingTime <= 0) {
            clearInterval(timerInterval);
            alert("Rest time is up! Get back to work!");
        }
    }, 1000);
}

function resetTimer() {
    clearInterval(timerInterval);
    const display = document.getElementById("timerDisplay");
    if (display) display.innerText = "01:00";
}

function updateTimerDisplay(seconds) {
    const display = document.getElementById("timerDisplay");
    if (!display) return;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    display.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// AI assistance: GitHub Copilot helped implement upload after picture selection.
const profilePictureForm = document.getElementById('profilePictureForm');
const profilePictureInput = document.getElementById('profilePictureInput');
const chooseProfilePicture = document.getElementById('chooseProfilePicture');

if (profilePictureForm && profilePictureInput && chooseProfilePicture) {
    chooseProfilePicture.addEventListener('click', function() {
        profilePictureInput.click();
    });

    profilePictureInput.addEventListener('change', function() {
        if (profilePictureInput.files.length > 0) {
            profilePictureForm.requestSubmit();
        }
    });
}

// AI assistance: GitHub Copilot helped connect calculator output to nutrition targets.
const nutritionCalculatorForm = document.getElementById('calcForm');
if (nutritionCalculatorForm) {
    const calculatorOutput = document.getElementById('calcResult');

    function updateNutritionTargets() {
        const result = calculatorOutput.textContent.match(/([\d,]+)\s*kcal\/day/i);
        if (!result) return;

        const maintenance = Number(result[1].replace(/,/g, ''));
        const bodyWeightKg = Number(document.getElementById('weight').value);
        if (!Number.isFinite(bodyWeightKg) || bodyWeightKg <= 0) return;

        const plans = [
            { key: 'cut', calories: Math.round(maintenance * 0.85) },
            { key: 'planMaintenance', calories: maintenance },
            { key: 'bulk', calories: Math.round(maintenance * 1.10) }
        ];

        plans.forEach(function(plan) {
            const protein = Math.round(bodyWeightKg * 1.6);
            const remainingCalories = Math.max(plan.calories - protein * 4, 0);
            const carbs = Math.round(remainingCalories / 7);
            const fats = Math.round(remainingCalories / 21);

            document.getElementById(`${plan.key}Calories`).textContent =
                plan.calories.toLocaleString();
            document.getElementById(`${plan.key}Protein`).textContent = protein;
            document.getElementById(`${plan.key}Carbs`).textContent = carbs;
            document.getElementById(`${plan.key}Fats`).textContent = fats;
        });

        document.getElementById('maintenanceCalories').textContent =
            document.getElementById('planMaintenanceCalories').textContent;
        document.getElementById('maintenanceProtein').textContent =
            document.getElementById('planMaintenanceProtein').textContent;
        document.getElementById('maintenanceCarbs').textContent =
            document.getElementById('planMaintenanceCarbs').textContent;
        document.getElementById('maintenanceFats').textContent =
            document.getElementById('planMaintenanceFats').textContent;
    }

    nutritionCalculatorForm.addEventListener('submit', function() {
        window.setTimeout(updateNutritionTargets, 0);
    });
}

