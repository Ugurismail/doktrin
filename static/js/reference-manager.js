/**
 * Kaynakça Yönetim Sistemi
 * Doktrin platformu için akademik kaynak ekleme ve atıf yapma sistemi
 */

// Global variables
let selectedReferences = [];
let allReferences = [];

// Modal işlemleri
function openReferenceModal() {
    const modal = document.getElementById('referenceModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeReferenceModal() {
    const modal = document.getElementById('referenceModal');
    if (modal) {
        modal.classList.remove('active');
        clearReferenceForm();
    }
}

function showAllReferences() {
    const modal = document.getElementById('allReferencesModal');
    if (modal) {
        modal.classList.add('active');
        loadAllReferencesForSelection();
    }
}

function closeAllReferencesModal() {
    const modal = document.getElementById('allReferencesModal');
    if (modal) {
        modal.classList.remove('active');
    }
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
        document.getElementById('saveRefBtn').style.display = 'inline-block';
    } else {
        newTab.classList.remove('active');
        existingTab.classList.add('active');
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
        document.getElementById('saveRefBtn').style.display = 'none';
        loadExistingReferences();
    }
}

// Tüm kaynakları yükle (modal içinde seçim için)
function loadExistingReferences() {
    fetch('/doctrine/api/references/list/')
        .then(response => response.json())
        .then(data => {
            allReferences = data.references;
            displayReferenceList(allReferences, 'referenceList', false);
        })
        .catch(error => {
            console.error('Kaynaklar yüklenirken hata:', error);
            document.getElementById('referenceList').innerHTML = '<p class="text-danger">Kaynaklar yüklenemedi</p>';
        });
}

// Kaynaklar butonuna tıklandığında (hızlı seçim için)
function loadAllReferencesForSelection() {
    fetch('/doctrine/api/references/list/')
        .then(response => response.json())
        .then(data => {
            allReferences = data.references;
            displayReferenceList(allReferences, 'allReferenceList', true);
        })
        .catch(error => {
            console.error('Kaynaklar yüklenirken hata:', error);
            document.getElementById('allReferenceList').innerHTML = '<p class="text-danger">Kaynaklar yüklenemedi</p>';
        });
}

// Yeni kaynak kaydet
function saveNewReference() {
    const form = document.getElementById('newReferenceForm');

    // Form validation
    const author = document.getElementById('ref_author').value.trim();
    const title = document.getElementById('ref_title').value.trim();
    const year = document.getElementById('ref_year').value;

    if (!author || !title || !year) {
        alert('Lütfen gerekli alanları doldurun (Yazar, Başlık, Yıl)');
        return;
    }

    const referenceData = {
        reference_type: document.getElementById('ref_type').value,
        author: author,
        title: title,
        year: parseInt(year),
        publisher: document.getElementById('ref_publisher').value.trim(),
        city: document.getElementById('ref_city').value.trim(),
        url: document.getElementById('ref_url').value.trim(),
        notes: document.getElementById('ref_notes').value.trim(),
        page_number: document.getElementById('ref_page').value.trim(),
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
            alert('Hata: ' + (data.error || 'Bilinmeyen hata'));
        }
    })
    .catch(error => {
        console.error('Kaynak kaydedilirken hata:', error);
        alert('Kaynak kaydedilirken hata oluştu: ' + error);
    });
}

// Kaynak listesini göster
function displayReferenceList(references, containerId, showActions) {
    const container = document.getElementById(containerId);
    if (!container) return;

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
                    <div class="reference-author">${escapeHtml(ref.author)} (${ref.year})</div>
                    <div class="reference-title">${escapeHtml(ref.title)}</div>
                    ${ref.publisher ? `<div class="reference-publisher">${escapeHtml(ref.publisher)}</div>` : ''}
                    ${ref.url ? `<div class="reference-url"><a href="${escapeHtml(ref.url)}" target="_blank">🔗 Link</a></div>` : ''}
                    ${ref.created_by ? `<div class="reference-meta">Ekleyen: ${escapeHtml(ref.created_by)}</div>` : ''}
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
    const ref = allReferences.find(r => r.id === refId);
    if (ref) {
        addReferenceToSelected(ref);
        closeReferenceModal();
        closeAllReferencesModal();
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

    if (!container || !list) return;

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
                    <strong>${escapeHtml(ref.author)} (${ref.year})</strong>. ${escapeHtml(ref.title)}.
                    ${ref.page_number ? ` ${escapeHtml(ref.page_number)}` : ''}
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
    if (input) {
        input.value = JSON.stringify(selectedReferences.map(r => ({
            id: r.id,
            page_number: r.page_number || ''
        })));
    }
}

// Atıf ekle (metin içine)
function insertCitation(refId) {
    const ref = allReferences.find(r => r.id === refId);
    if (!ref) return;

    const textarea = document.getElementById('justification');
    if (!textarea) return;

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
    const authorLast = ref.author.includes(',') ? ref.author.split(',')[0].trim() : ref.author.split(' ')[0];
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
    displayReferenceList(filtered, 'referenceList', false);
}

function searchAllReferences() {
    const searchTerm = document.getElementById('searchAllReference').value.toLowerCase();
    const filtered = allReferences.filter(ref =>
        ref.author.toLowerCase().includes(searchTerm) ||
        ref.title.toLowerCase().includes(searchTerm) ||
        ref.year.toString().includes(searchTerm)
    );
    displayReferenceList(filtered, 'allReferenceList', true);
}

// Form temizle
function clearReferenceForm() {
    const form = document.getElementById('newReferenceForm');
    if (form) {
        form.reset();
    }
}

// HTML escape helper
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
window.addEventListener('click', function(event) {
    const refModal = document.getElementById('referenceModal');
    const allRefModal = document.getElementById('allReferencesModal');

    if (event.target === refModal) {
        closeReferenceModal();
    }
    if (event.target === allRefModal) {
        closeAllReferencesModal();
    }
});
