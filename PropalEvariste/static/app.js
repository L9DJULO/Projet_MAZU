const form = document.getElementById("vision-form");
const modeSelect = document.getElementById("mode");
const azureConfig = document.getElementById("azure-config");
const azureKeyInput = document.getElementById("azure-key");
const imageInput = document.getElementById("image-file");
const previewImage = document.getElementById("preview-image");
const previewCaption = document.getElementById("preview-caption");
const output = document.getElementById("output");
const priceOutput = document.getElementById("price-output");
const recommendationOutput = document.getElementById("recommendation-output");
const agentTranscript = document.getElementById("agent-transcript");
const statusPill = document.getElementById("status-pill");
const submitButton = document.getElementById("submit-btn");
const vehiclePanel = document.getElementById("vehicle-panel");
const estimatedConditionLabel = document.getElementById("estimated-condition");
const vehicleForm = document.getElementById("vehicle-form");
const vehicleSubmitButton = document.getElementById("vehicle-submit-btn");
const vehicleModelInput = document.getElementById("vehicle-model");
const vehicleYearInput = document.getElementById("vehicle-year");
const vehicleMileageInput = document.getElementById("vehicle-mileage");
const vehicleFuelInput = document.getElementById("vehicle-fuel");
const vehicleOwnersInput = document.getElementById("vehicle-owners");
const vehicleNewPriceInput = document.getElementById("vehicle-new-price");

const AZURE_IMAGE_ENDPOINT = "https://germanywestcentral.api.cognitive.microsoft.com/customvision/v3.0/Prediction/2d064853-11ce-4b07-81fa-0fb08975dcba/classify/iterations/Iteration1/image";
const LOCAL_IMAGE_ENDPOINT = "/api/image";
const VEHICLE_REPORT_ENDPOINT = "/api/vehicle-report";

let currentObjectUrl = null;
let latestPrediction = null;
let latestEstimatedCondition = null;

function setStatus(text, tone = "idle") {
  statusPill.textContent = text;
  statusPill.dataset.tone = tone;
}

function setOutput(value) {
  output.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function showAzureConfig() {
  azureConfig.classList.toggle("hidden", modeSelect.value !== "azure");
}

function formatPrediction(data) {
  const predictions = data.predictions ?? [];
  let result = "";

  predictions.forEach((element) => {
    result += `${element.tagName}: ${element.probability}\n`;
  });

  return result;
}

function getTopPrediction(data) {
  const predictions = data.predictions ?? [];

  return predictions.reduce((best, current) => {
    if (!best || current.probability > best.probability) {
      return current;
    }

    return best;
  }, null);
}

function estimateConditionFromPrediction(data) {
  const topPrediction = getTopPrediction(data);

  return {
    "label": topPrediction.tagName,
    "confidence": topPrediction.probability,
    "isInGoodCondition": topPrediction.tagName === "Good"
  };
}

function setPriceOutput(value) {
  priceOutput.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function setRecommendationOutput(value) {
  recommendationOutput.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function clearTranscript() {
  agentTranscript.innerHTML = '<p class="transcript-empty">La discussion apparaîtra ici une fois la recommandation générée.</p>';
}

function renderTranscript(messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    clearTranscript();
    return;
  }

  agentTranscript.innerHTML = "";

  messages.forEach((message, index) => {
    const block = document.createElement("article");
    block.className = "transcript-message";
    block.dataset.speaker = message.speaker ?? "Agent";

    const header = document.createElement("div");
    header.className = "transcript-message-header";

    const badge = document.createElement("span");
    badge.className = "transcript-speaker";
    badge.textContent = message.speaker ?? "Agent";

    const counter = document.createElement("span");
    counter.className = "transcript-counter";
    counter.textContent = `Message ${index + 1}`;

    header.append(badge, counter);

    const content = document.createElement("p");
    content.className = "transcript-content";
    content.textContent = message.content ?? "";

    block.append(header, content);
    agentTranscript.appendChild(block);
  });
}

function computeMockPrice(payload, condition) {
  const basePrice = Number(payload.vehicule.cout_achat_neuf_eur) || 0;
  const year = Number(payload.vehicule.annee) || 0;
  const mileage = Number(payload.vehicule.kilometrage_km) || 0;
  const owners = Number(payload.vehicule.nb_proprietaires) || 0;
  const age = Math.max(0, new Date().getFullYear() - year);

  const ageFactor = Math.max(0.35, 1 - age * 0.045);
  const mileageFactor = Math.max(0.4, 1 - mileage / 280000);
  const ownerFactor = Math.max(0.82, 1 - Math.max(0, owners - 1) * 0.035);
  const fuelFactor = {
    Essence: 1,
    Diesel: 0.98,
    Hybride: 1.05,
    Electrique: 1.08,
    GPL: 0.95,
  }[payload.vehicule.carburant] ?? 1;
  const conditionFactor = condition.isInGoodCondition ? 1.06 : 0.1;

  return Math.max(0, Math.round(basePrice * ageFactor * mileageFactor * ownerFactor * fuelFactor * conditionFactor));
}

function showVehiclePanel(condition) {
  latestEstimatedCondition = condition;
  estimatedConditionLabel.textContent = `${condition.label} (${Math.round(condition.confidence * 100)}%)`;
  vehiclePanel.classList.remove("hidden");
  setPriceOutput("Le prix estimé final apparaîtra ici.");
  setRecommendationOutput("La recommandation finale apparaîtra ici après l'analyse du dossier.");
  clearTranscript();
}

function updatePreview(file) {
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
  }

  currentObjectUrl = URL.createObjectURL(file);
  previewImage.src = currentObjectUrl;
  previewImage.alt = file.name;
  previewCaption.textContent = `${file.name} · ${Math.round(file.size / 1024)} Ko`;
}

modeSelect.addEventListener("change", showAzureConfig);

imageInput.addEventListener("change", () => {
  const [file] = imageInput.files ?? [];
  if (!file) {
    previewImage.removeAttribute("src");
    previewCaption.textContent = "Aucune image sélectionnée";
    return;
  }

  updatePreview(file);
});

vehicleForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!latestPrediction || !latestEstimatedCondition) {
    setStatus("Analyse requise", "error");
    setPriceOutput("Il faut d'abord lancer une prédiction avant d'envoyer le dossier.");
    return;
  }

  vehicleSubmitButton.disabled = true;
  setStatus("Envoi du dossier", "busy");

  const estimatedPrice = computeMockPrice(
    {
      vehicule: {
        modele: vehicleModelInput.value.trim(),
        annee: Number(vehicleYearInput.value),
        kilometrage_km: Number(vehicleMileageInput.value),
        carburant: vehicleFuelInput.value,
        nb_proprietaires: Number(vehicleOwnersInput.value),
        cout_achat_neuf_eur: Number(vehicleNewPriceInput.value),
      },
    },
    latestEstimatedCondition,
  );

  setPriceOutput(`${estimatedPrice.toLocaleString("fr-FR")} €`);
  setRecommendationOutput("Analyse multi-agents en cours...");
  clearTranscript();

  const payload = {
    vision_result: latestPrediction,
    etat_estime: latestEstimatedCondition,
    estimated_price_eur: estimatedPrice,
    vehicule: {
      modele: vehicleModelInput.value.trim(),
      annee: Number(vehicleYearInput.value),
      kilometrage_km: Number(vehicleMileageInput.value),
      carburant: vehicleFuelInput.value,
      nb_proprietaires: Number(vehicleOwnersInput.value),
      cout_achat_neuf_eur: Number(vehicleNewPriceInput.value),
    },
  };

  try {
    const response = await fetch(VEHICLE_REPORT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const responsePayload = await response.json();

    if (!response.ok) {
      throw new Error(responsePayload.message ?? JSON.stringify(responsePayload, null, 2));
    }

    setStatus("Dossier envoyé", "success");
    setRecommendationOutput(responsePayload.recommendation ?? "Aucune recommandation n'a été renvoyée.");
    console.log(responsePayload);
    renderTranscript(responsePayload.transcript ?? []);
  } catch (error) {
    setStatus("Erreur", "error");
    setPriceOutput(error instanceof Error ? error.message : String(error));
    setRecommendationOutput("Impossible de générer une recommandation.");
    clearTranscript();
  } finally {
    vehicleSubmitButton.disabled = false;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const [file] = imageInput.files ?? [];
  if (!file) {
    setStatus("Image requise", "error");
    setOutput("Choisis une image avant d'envoyer la requête.");
    return;
  }

  submitButton.disabled = true;
  setStatus("Analyse en cours", "busy");
  setOutput("Envoi de l'image...");

  try {
    const mode = modeSelect.value;
    let response;

    if (mode === "azure") {
      const apiKey = azureKeyInput.value.trim();
      if (!apiKey) {
        throw new Error("La clé Azure est obligatoire en mode cloud.");
      }

      response = await fetch(AZURE_IMAGE_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
          "Prediction-Key": apiKey,
        },
        body: await file.arrayBuffer(),
      });
    } else {
      response = await fetch(LOCAL_IMAGE_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
        },
        body: await file.arrayBuffer(),
      });
    }

    const contentType = response.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();

    if (!response.ok) {
      throw new Error(typeof payload === "string" ? payload : JSON.stringify(payload, null, 2));
    }

    latestPrediction = payload;

    const condition = estimateConditionFromPrediction(payload);
    setOutput(`${formatPrediction(payload)}\nÉtat estimé: ${condition.label}`);
    setStatus("Détails requis", "success");
    showVehiclePanel(condition);
  } catch (error) {
    setStatus("Erreur", "error");
    setOutput(error instanceof Error ? error.message : String(error));
  } finally {
    submitButton.disabled = false;
  }
});

showAzureConfig();