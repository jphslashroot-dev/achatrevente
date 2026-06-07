// JavaScript - Gestion de l'interactivité pour le Tableau de Bord AchatRevente Pro

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initToasts();
    
    // Écouteur pour adapter dynamiquement la modale selon le statut
    const statusSelect = document.getElementById('form_status');
    if (statusSelect) {
        statusSelect.addEventListener('change', toggleSaleDateVisibility);
    }
});

// ==========================================
// 1. GESTION DES THÈMES (SOMBRE / CLAIR)
// ==========================================
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';

    if (currentTheme === 'light') {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        if (themeToggle) themeToggle.checked = false;
    } else {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        if (themeToggle) themeToggle.checked = true;
    }

    if (themeToggle) {
        themeToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                document.body.classList.remove('light-theme');
                document.body.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.remove('dark-theme');
                document.body.classList.add('light-theme');
                localStorage.setItem('theme', 'light');
            }
        });
    }
}

// ==========================================
// 2. GESTION DES NOTIFICATIONS (TOASTS)
// ==========================================
function initToasts() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        // Auto-fermeture après 5 secondes
        setTimeout(() => {
            dismissToast(toast);
        }, 5000);
    });
}

function closeToast(button) {
    const toast = button.closest('.toast');
    dismissToast(toast);
}

function dismissToast(toast) {
    if (!toast) return;
    toast.style.transform = 'translateX(120%)';
    toast.style.opacity = '0';
    setTimeout(() => {
        toast.remove();
    }, 300);
}

// ==========================================
// 3. GESTION DE LA FENÊTRE MODALE (AJOUT / ÉDITION)
// ==========================================
const modal = document.getElementById('itemModal');
const modalTitle = document.getElementById('modalTitle');
const itemForm = document.getElementById('itemForm');
const modalSubmitBtn = document.getElementById('modalSubmitBtn');
const uploadLabel = document.getElementById('uploadLabel');

// Basculer l'affichage du champ "Date de revente" selon le statut choisi
function toggleSaleDateVisibility() {
    const statusSelect = document.getElementById('form_status');
    const saleDateGroup = document.getElementById('form_sale_date_group');
    if (statusSelect && saleDateGroup) {
        if (statusSelect.value === 'Vendu') {
            saleDateGroup.classList.remove('hidden');
        } else {
            saleDateGroup.classList.add('hidden');
        }
    }
}

// Ouvrir en mode Ajout
function openAddModal() {
    modalTitle.textContent = "Ajouter un nouvel objet";
    itemForm.action = "/add";
    modalSubmitBtn.textContent = "Ajouter";
    
    // Réinitialiser les champs du formulaire
    itemForm.reset();
    removePreview();
    
    // Mettre la date d'achat par défaut sur aujourd'hui
    const today = new Date().toISOString().split('T')[0];
    const purchaseDateInput = document.getElementById('form_purchase_date');
    if (purchaseDateInput) {
        purchaseDateInput.value = today;
    }
    
    // Réinitialiser le vendeur et le site de vente
    const sellerInput = document.getElementById('form_seller');
    if (sellerInput) {
        sellerInput.value = '';
    }
    const platformInput = document.getElementById('form_platform');
    if (platformInput) {
        platformInput.value = '';
    }
    
    toggleSaleDateVisibility();
    
    // Afficher la modale
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Bloquer le défilement
}

// Ouvrir en mode Édition (supporte maintenant les dates d'achat, de revente, le vendeur et la plateforme)
function openEditModal(id, name, description, purchasePrice, salePrice, status, purchaseDate, saleDate, seller, platform) {
    modalTitle.textContent = "Modifier l'objet";
    itemForm.action = `/edit/${id}`;
    modalSubmitBtn.textContent = "Enregistrer";

    // Pré-remplir les champs du formulaire
    document.getElementById('form_name').value = name;
    document.getElementById('form_description').value = description;
    document.getElementById('form_purchase_price').value = purchasePrice;
    document.getElementById('form_sale_price').value = salePrice || '';
    document.getElementById('form_status').value = status;
    
    const purchaseDateInput = document.getElementById('form_purchase_date');
    if (purchaseDateInput) {
        purchaseDateInput.value = purchaseDate || '';
    }
    
    const saleDateInput = document.getElementById('form_sale_date');
    if (saleDateInput) {
        saleDateInput.value = saleDate || '';
    }

    const sellerInput = document.getElementById('form_seller');
    if (sellerInput) {
        sellerInput.value = seller || '';
    }

    const platformInput = document.getElementById('form_platform');
    if (platformInput) {
        platformInput.value = platform || '';
    }

    // Réinitialiser l'input file & preview
    removePreview();
    
    toggleSaleDateVisibility();

    // Afficher la modale
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Bloquer le défilement
}

// Fermer la modale
function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = ''; // Rétablir le défilement
    stopCamera(); // Arrêter le flux de la caméra si actif
}

// Fermer en cliquant en dehors de la carte modale
if (modal) {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// ==========================================
// 3b. GESTION DES ONGLETS (TABS)
// ==========================================
function switchTab(tabId) {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        if (btn.getAttribute('onclick').includes(tabId)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    tabContents.forEach(content => {
        if (content.id === tabId) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// ==========================================
// 4. PRÉVISUALISATION DE L'IMAGE
// ==========================================
function previewImage(input) {
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImage = document.getElementById('imagePreview');
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        
        // Mettre à jour le label
        uploadLabel.textContent = file.name;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewContainer.classList.remove('hidden');
        }
        reader.readAsDataURL(file);
    }
}

function removePreview() {
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImage = document.getElementById('imagePreview');
    const fileInput = document.getElementById('form_image');
    const base64Input = document.getElementById('form_image_base64');
    
    if (fileInput) fileInput.value = '';
    if (base64Input) base64Input.value = '';
    if (uploadLabel) uploadLabel.textContent = "Choisir un fichier";
    if (previewImage) previewImage.src = '#';
    if (previewContainer) previewContainer.classList.add('hidden');
}

// ==========================================
// 5. CONTRÔLE DE LA CAMÉRA WEB
// ==========================================
let cameraStreamObject = null;

function startCamera() {
    const cameraContainer = document.getElementById('cameraContainer');
    const cameraStream = document.getElementById('cameraStream');
    
    if (!cameraContainer || !cameraStream) return;
    
    if (cameraStreamObject) return; // Déjà démarrée
    
    navigator.mediaDevices.getUserMedia({ 
        video: { 
            facingMode: 'environment', // Préférer la caméra dorsale sur smartphone
            width: { ideal: 640 },
            height: { ideal: 480 }
        } 
    })
    .then(stream => {
        cameraStreamObject = stream;
        cameraStream.srcObject = stream;
        cameraStream.play();
        cameraContainer.classList.remove('hidden');
        
        // Vider l'aperçu existant classique
        removePreview();
    })
    .catch(err => {
        alert("Impossible d'accéder à la caméra : " + err.message);
    });
}

function stopCamera() {
    const cameraContainer = document.getElementById('cameraContainer');
    const cameraStream = document.getElementById('cameraStream');
    
    if (cameraStreamObject) {
        cameraStreamObject.getTracks().forEach(track => track.stop());
        cameraStreamObject = null;
    }
    
    if (cameraStream) {
        cameraStream.srcObject = null;
    }
    
    if (cameraContainer) {
        cameraContainer.classList.add('hidden');
    }
}

function capturePhoto() {
    const cameraStream = document.getElementById('cameraStream');
    const base64Input = document.getElementById('form_image_base64');
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImage = document.getElementById('imagePreview');
    
    if (!cameraStream || !cameraStreamObject) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = cameraStream.videoWidth || 640;
    canvas.height = cameraStream.videoHeight || 480;
    
    const ctx = canvas.getContext('2d');
    
    // Effet miroir sur le canvas pour correspondre au rendu vidéo miroir
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    
    ctx.drawImage(cameraStream, 0, 0, canvas.width, canvas.height);
    
    const dataURL = canvas.toDataURL('image/jpeg', 0.9);
    
    if (base64Input) {
        base64Input.value = dataURL;
    }
    
    if (previewImage) {
        previewImage.src = dataURL;
    }
    
    if (previewContainer) {
        previewContainer.classList.remove('hidden');
    }
    
    if (uploadLabel) {
        uploadLabel.textContent = "Photo capturée avec la caméra";
    }
    
    stopCamera();
}

// ==========================================
// 6. GESTION DE LA MODALE DES VENDEURS
// ==========================================
const sellersModal = document.getElementById('sellersModal');

function openSellersModal() {
    if (sellersModal) {
        sellersModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeSellersModal() {
    if (sellersModal) {
        sellersModal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

if (sellersModal) {
    sellersModal.addEventListener('click', (e) => {
        if (e.target === sellersModal) {
            closeSellersModal();
        }
    });
}

// ==========================================
// 7. VENTE RAPIDE (QUICK SELL)
// ==========================================
const quickSellModal = document.getElementById('quickSellModal');

function quickSell(itemId, purchasePrice) {
    const quickSellForm = document.getElementById('quickSellForm');
    const quickSalePriceInput = document.getElementById('quick_sale_price');
    const purchasePriceHint = document.getElementById('quickSellPurchasePriceHint');

    if (quickSellForm && quickSalePriceInput && quickSellModal) {
        // Configurer l'action du formulaire et pré-remplir les données de l'objet
        quickSellForm.action = `/quick_sell/${itemId}`;
        quickSalePriceInput.value = purchasePrice;
        if (purchasePriceHint) {
            purchasePriceHint.textContent = `Prix d'achat initial : ${purchasePrice} €`;
        }

        // Ouvrir la modale
        quickSellModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Mettre le focus automatique sur l'input de prix
        setTimeout(() => {
            quickSalePriceInput.focus();
            quickSalePriceInput.select();
        }, 100);
    }
}

function closeQuickSellModal() {
    if (quickSellModal) {
        quickSellModal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

if (quickSellModal) {
    quickSellModal.addEventListener('click', (e) => {
        if (e.target === quickSellModal) {
            closeQuickSellModal();
        }
    });
}

// ==========================================
// 8. MODALE DE CONFIRMATION DE SUPPRESSION
// ==========================================
const confirmDeleteModal = document.getElementById('confirmDeleteModal');
let pendingDeleteUrl = '';

function showConfirmDelete(actionUrl, message) {
    const confirmMessage = document.getElementById('confirmDeleteMessage');
    
    if (confirmDeleteModal && confirmMessage) {
        pendingDeleteUrl = actionUrl;
        confirmMessage.textContent = message;
        
        // Ouvrir la modale
        confirmDeleteModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeConfirmDeleteModal() {
    if (confirmDeleteModal) {
        confirmDeleteModal.classList.remove('active');
        document.body.style.overflow = '';
        pendingDeleteUrl = '';
    }
}

// Action de validation de suppression
const confirmDeleteSubmitBtn = document.getElementById('confirmDeleteSubmitBtn');
if (confirmDeleteSubmitBtn) {
    confirmDeleteSubmitBtn.addEventListener('click', () => {
        if (pendingDeleteUrl) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = pendingDeleteUrl;
            document.body.appendChild(form);
            form.submit();
        }
    });
}

if (confirmDeleteModal) {
    confirmDeleteModal.addEventListener('click', (e) => {
        if (e.target === confirmDeleteModal) {
            closeConfirmDeleteModal();
        }
    });
}
