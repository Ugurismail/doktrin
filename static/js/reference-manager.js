/**
 * Kaynakça Yönetim Sistemi
 * Doktrin platformu için akademik kaynak ekleme ve atıf yapma sistemi
 */

// Global variables
let selectedReferences = [];
let allReferences = [];
let myReferences = [];

// Modal işlemleri
function openReferenceModal() {
    document.getElementById('referenceModal').classList.add('active');
    loadAllReferences();
}

function closeReferenceModal() {
    document.getElementById('referenceModal').classList.remove('active');
    clearReferenceForm();
}

function showMyReferences() {
    document.getElementById('myReferencesModal').classList.add('active');
    loadMyReferences();
}

function closeMyReferencesModal() {
    document.getElementById('myReferencesModal').classList.remove('active');
}

// Tab switching
function switchTab(tabName) {
    const newTab = document.getElementById('newReferenceTab');
    const existingTab = document.getElementById('existingReferenceTab');
    const tabs = document.querySelectorAll('.tab-btn');

    if (tabName === 'new') {
        newTab.classList.add('active');
        existingTab.classList.remove('active');
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
        document.getElementById('saveRefBtn').textContent = 'Kaydet ve Ekle';
    } else {
        newTab.classList.remove('active');
        existingTab.classList.add('active');
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
        document.getElementById('saveRefBtn').style.display = 'none';
        loadAllReferences();
    }
}

// Yeni kaynak kaydet
function saveNewReference() {
    const form = document.getElementById('newReferenceForm');

    if (!form.checkValidity()) {
        alert('Lütfen gerekli alanları doldurun (*, yazar, başlık, yıl)');
        return;
    }

    const referenceData = {
        reference_type: document.getElementById('ref_type').value,
        author: document.getElementById('ref_author').value,
        title: document.getElementById('ref_title').value,
        year: document.getElementById('ref_year').value,
        publisher: document.getElementById('ref_publisher').value,
        city: document.getElementById('ref_city').value,
        url: document.getElementById('ref_url').value,
        notes: document.getElementById('ref_notes').value,
        page_number: document.getElementById('ref_page').value,
    };

    fetch('/doctrine/api/references/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(referenceData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addReferenceToSelected(data.reference);
            closeReferenceModal();
            alert('✓ Kaynak başarıyla eklendi!');
        } else {
            alert('Hata: ' + data.error);
        }
    })
    .catch(error => {
        alert('Kaynak kaydedilirken hata oluştu: ' + error);
    });
}

// Tüm kaynakları yükle
function loadAllReferences() {
    fetch('/doctrine/api/references/list/')
        .then(response => response.json())
        .then(data => {
            allReferences = data.references;
            displayReferenceList(allReferences, 'referenceList');
        })
        .catch(error => {
            document.getElementById('referenceList').innerHTML = '<p class="text-danger">Kaynaklar yüklenemedi</p>';
        });
}

// Kullanıcının kendi kaynaklarını yükle
function loadMyReferences() {
    fetch('/doctrine/api/references/my-references/')
        .then(response => response.json())
        .then(data => {
            myReferences = data.references;
            displayReferenceList(myReferences, 'myReferenceList', true);
        })
        .catch(error => {
            document.getElementById('myReferenceList').innerHTML = '<p class="text-danger">Kaynaklar yüklenemedi</p>';
        });
}

// Kaynak listesini göster
function displayReferenceList(references, containerId, showActions = false) {
    const container = document.getElementById(containerId);

    if (references.length === 0) {
        container.innerHTML = '<p class="text-muted">Henüz kaynak bulunmuyor</p>';
        return;
    }

    let html = '';
    references.forEach(ref => {
        const isSelected = selectedReferences.some(r => r.id === ref.id);
        html += `
            <div class="reference-item ${isSelected ? 'selected' : ''}" data-ref-id="${ref.id}">
                <div class="reference-info">
                    <div class="reference-author">${ref.author} (${ref.year})</div>
                    <div class="reference-title">${ref.title}</div>
                    ${ref.publisher ? `<div class="reference-publisher">${ref.publisher}</div>` : ''}
                    ${ref.url ? `<div class="reference-url"><a href="${ref.url}" target="_blank">🔗 ${ref.url}</a></div>` : ''}
                </div>
                <div class="reference-actions">
                    ${!isSelected ? `
                        <button type="button" class="btn btn-sm btn-primary" onclick="selectReference(${ref.id})">
                            Seç
                        </button>
                    ` : `
                        <span class="badge badge-success">✓ Seçili</span>
                    `}
                    ${showActions ? `
                        <button type="button" class="btn btn-sm btn-secondary" onclick="insertCitation(${ref.id})">
                            Atıf Ekle
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Kaynağı seçili listeye ekle
function selectReference(refId) {
    const ref = allReferences.find(r => r.id === refId) || myReferences.find(r => r.id === refId);
    if (ref) {
        addReferenceToSelected(ref);
        closeReferenceModal();
    }
}

function addReferenceToSelected(reference) {
    // Zaten ekli mi kontrol et
    if (selectedReferences.some(r => r.id === reference.id)) {
        alert('Bu kaynak zaten eklenmiş');
        return;
    }

    selectedReferences.push(reference);
    updateSelectedReferencesList();
    updateHiddenInput();
}

// Seçili kaynakları göster
function updateSelectedReferencesList() {
    const container = document.getElementById('selected-references-container');
    const list = document.getElementById('selected-references-list');

    if (selectedReferences.length === 0) {
        container.classList.add('hidden');
        return;
    }

    container.classList.remove('hidden');
    let html = '';

    selectedReferences.forEach((ref, index) => {
        html += `
            <div class="selected-reference-item">
                <div class="reference-number">[${index + 1}]</div>
                <div class="reference-info">
                    <strong>${ref.author} (${ref.year})</strong>. ${ref.title}.
                    ${ref.page_number ? ` ${ref.page_number}` : ''}
                </div>
                <div class="reference-actions">
                    <button type="button" class="btn btn-sm btn-secondary" onclick="insertCitationById(${ref.id})">
                        Atıf Ekle
                    </button>
                    <button type="button" class="btn btn-sm btn-danger" onclick="removeReference(${ref.id})">
                        ✕
                    </button>
                </div>
            </div>
        `;
    });

    list.innerHTML = html;
}

// Kaynağı listeden çıkar
function removeReference(refId) {
    selectedReferences = selectedReferences.filter(r => r.id !== refId);
    updateSelectedReferencesList();
    updateHiddenInput();
}

// Hidden input'u güncelle (form submit için)
function updateHiddenInput() {
    const input = document.getElementById('selected_references');
    input.value = JSON.stringify(selectedReferences.map(r => ({
        id: r.id,
        page_number: r.page_number || ''
    })));
}

// Atıf ekle (metin içine)
function insertCitation(refId) {
    const ref = allReferences.find(r => r.id === refId) || myReferences.find(r => r.id === refId);
    if (!ref) return;

    const textarea = document.getElementById('justification');
    const citation = getCitationText(ref);

    // Cursor pozisyonuna ekle
    const startPos = textarea.selectionStart;
    const endPos = textarea.selectionEnd;
    const textBefore = textarea.value.substring(0, startPos);
    const textAfter = textarea.value.substring(endPos);

    textarea.value = textBefore + citation + textAfter;
    textarea.selectionStart = textarea.selectionEnd = startPos + citation.length;
    textarea.focus();
}

function insertCitationById(refId) {
    const ref = selectedReferences.find(r => r.id === refId);
    if (ref) {
        insertCitation(refId);
    }
}

// Atıf metnini oluştur
function getCitationText(ref) {
    const authorLast = ref.author.includes(',') ? ref.author.split(',')[0] : ref.author.split(' ')[0];
    let citation = `(${authorLast}, ${ref.year}`;
    if (ref.page_number) {
        citation += `, ${ref.page_number}`;
    }
    citation += ')';
    return citation;
}

// Arama fonksiyonları
function searchReferences() {
    const searchTerm = document.getElementById('searchReference').value.toLowerCase();
    const filtered = allReferences.filter(ref =>
        ref.author.toLowerCase().includes(searchTerm) ||
        ref.title.toLowerCase().includes(searchTerm) ||
        ref.year.toString().includes(searchTerm)
    );
    displayReferenceList(filtered, 'referenceList');
}

function searchMyReferences() {
    const searchTerm = document.getElementById('searchMyReference').value.toLowerCase();
    const filtered = myReferences.filter(ref =>
        ref.author.toLowerCase().includes(searchTerm) ||
        ref.title.toLowerCase().includes(searchTerm) ||
        ref.year.toString().includes(searchTerm)
    );
    displayReferenceList(filtered, 'myReferenceList', true);
}

// Form temizle
function clearReferenceForm() {
    document.getElementById('newReferenceForm').reset();
}

// CSRF token helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Modal dışına tıklanınca kapat
window.onclick = function(event) {
    const refModal = document.getElementById('referenceModal');
    const myRefModal = document.getElementById('myReferencesModal');

    if (event.target === refModal) {
        closeReferenceModal();
    }
    if (event.target === myRefModal) {
        closeMyReferencesModal();
    }
}
