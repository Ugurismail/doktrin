/**
 * Kaynakça Yönetim Sistemi
 * Doktrin platformu için akademik kaynak ekleme ve atıf yapma sistemi
 */

// Global variables
let selectedReferences = [];
let allReferences = [];
let authorsList = [];

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
function switchReferenceTab(tabName) {
    const newTab = document.getElementById('newReferenceTab');
    const existingTab = document.getElementById('existingReferenceTab');
    const tabs = document.querySelectorAll('.reference-modal .tab-btn');

    // Güvenlik kontrolü - elementler var mı?
    if (!newTab || !existingTab) {
        console.error('Reference tabs not found in DOM');
        return;
    }

    if (tabName === 'new') {
        newTab.classList.add('active');
        existingTab.classList.remove('active');
        if (tabs[0]) tabs[0].classList.add('active');
        if (tabs[1]) tabs[1].classList.remove('active');
        const saveBtn = document.getElementById('saveRefBtn');
        if (saveBtn) {
            saveBtn.textContent = 'Kaydet ve Ekle';
            saveBtn.style.display = 'inline-block';
        }
    } else {
        newTab.classList.remove('active');
        existingTab.classList.add('active');
        if (tabs[0]) tabs[0].classList.remove('active');
        if (tabs[1]) tabs[1].classList.add('active');
        const saveBtn = document.getElementById('saveRefBtn');
        if (saveBtn) saveBtn.style.display = 'none';
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
    // Form validation - yazar listesi kontrolü
    if (authorsList.length === 0) {
        if (window.showToast) {
            window.showToast('Lütfen en az bir yazar ekleyin', 'error', 3000);
        } else {
            alert('Lütfen en az bir yazar ekleyin');
        }
        return;
    }

    const title = document.getElementById('ref_title').value.trim();
    const year = document.getElementById('ref_year').value;

    if (!title || !year) {
        if (window.showToast) {
            window.showToast('Lütfen gerekli alanları doldurun (Başlık, Yıl)', 'error', 3000);
        } else {
            alert('Lütfen gerekli alanları doldurun (Başlık, Yıl)');
        }
        return;
    }

    // Yazarları birleştir (birden fazla yazar varsa " & " ile)
    const author = authorsList.join(' & ');

    const referenceData = {
        reference_type: document.getElementById('ref_type').value,
        author: author,
        title: title,
        year: parseInt(year),
        publisher: document.getElementById('ref_publisher').value.trim(),
        city: document.getElementById('ref_city').value.trim(),
        url: document.getElementById('ref_url').value.trim(),
        notes: document.getElementById('ref_notes').value.trim(),
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
            // Yeni kaynak eklendi, modal'ı kapat
            // NOT: Kaynak listeye eklenmiyor, sadece veritabanına kaydediliyor
            closeReferenceModal();
            if (window.showToast) {
                window.showToast('✓ Kaynak başarıyla oluşturuldu! Atıf eklemek için Kaynaklar butonunu kullanın.', 'success', 3000);
            }
        } else {
            if (window.showToast) {
                window.showToast('Hata: ' + (data.error || 'Bilinmeyen hata'), 'error', 3000);
            } else {
                alert('Hata: ' + (data.error || 'Bilinmeyen hata'));
            }
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

    // Kaynakları yazar soyadına göre sırala
    const sortedReferences = [...references].sort((a, b) => {
        const getLastName = (author) => {
            // "Soyadı, Ad" formatı varsa
            if (author.includes(',')) {
                return author.split(',')[0].trim().toLowerCase();
            }
            // "Ad Soyad" formatı varsa, son kelimeyi al
            const parts = author.trim().split(' ');
            return parts[parts.length - 1].toLowerCase();
        };

        const lastNameA = getLastName(a.author);
        const lastNameB = getLastName(b.author);

        return lastNameA.localeCompare(lastNameB, 'tr');
    });

    // Modal içindeki "Mevcut Kaynak Seç" sekmesi mi?
    const isSelectionMode = containerId === 'referenceList';

    let html = '';
    sortedReferences.forEach(ref => {
        const isSelected = selectedReferences.some(r => r.id === ref.id);
        html += `
            <div class="reference-item-compact ${isSelected ? 'selected' : ''}" data-ref-id="${ref.id}">
                <div class="reference-info-compact">
                    <strong>${escapeHtml(ref.author)}</strong> (${ref.year}). <em>${escapeHtml(ref.title)}</em>
                    ${ref.publisher ? ` - ${escapeHtml(ref.publisher)}` : ''}
                </div>
                <div class="reference-actions-compact">
                    ${isSelectionMode ? (
                        !isSelected ? `
                            <button type="button" class="btn btn-sm btn-primary" onclick="selectReference(${ref.id})">
                                Seç
                            </button>
                        ` : `
                            <span class="badge badge-success">✓ Seçili</span>
                        `
                    ) : ''}
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
        // Toast göster
        if (window.showToast) {
            window.showToast('✓ Kaynak seçildi', 'success', 2000);
        }
        // Modal'ları kapat
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

// Atıf ekle (metin içine) - Sayfa numarası opsiyonel modal ile sor
function insertCitation(refId) {
    const ref = allReferences.find(r => r.id === refId);
    if (!ref) return;

    const textarea = document.getElementById('justification');
    if (!textarea) return;

    // Sayfa numarası sor (opsiyonel)
    const pageNum = prompt('Sayfa numarası (opsiyonel, örn: s.157):', '');

    const citation = getCitationTextWithPage(ref, pageNum);

    // Cursor pozisyonuna ekle
    const startPos = textarea.selectionStart;
    const endPos = textarea.selectionEnd;
    const textBefore = textarea.value.substring(0, startPos);
    const textAfter = textarea.value.substring(endPos);

    textarea.value = textBefore + citation + textAfter;
    textarea.selectionStart = textarea.selectionEnd = startPos + citation.length;
    textarea.focus();

    // Kaynağı seçili kaynaklar listesine ekle (eğer yoksa)
    if (!selectedReferences.some(r => r.id === ref.id)) {
        selectedReferences.push({
            ...ref,
            page_number: pageNum || ''
        });
        updateSelectedReferencesList();
    }

    // Toast bildirimi göster
    if (window.showToast) {
        window.showToast('✓ Atıf eklendi ve kaynak listeye eklendi', 'success', 2000);
    }
}

function insertCitationById(refId) {
    const ref = selectedReferences.find(r => r.id === refId);
    if (ref) {
        insertCitation(refId);
    }
}

// Atıf metnini oluştur
function getCitationText(ref) {
    // Birden fazla yazar var mı kontrol et (" & " ile ayrılmış)
    const hasMultipleAuthors = ref.author.includes(' & ');

    let authorPart;
    if (hasMultipleAuthors) {
        // İlk yazarın soyadını al ve "vd." ekle
        const firstAuthor = ref.author.split(' & ')[0].trim();
        const authorLast = firstAuthor.includes(',') ? firstAuthor.split(',')[0].trim() : firstAuthor.split(' ')[0];
        authorPart = `${authorLast} vd.`;
    } else {
        // Tek yazar
        authorPart = ref.author.includes(',') ? ref.author.split(',')[0].trim() : ref.author.split(' ')[0];
    }

    let citation = `(${authorPart}, ${ref.year}`;
    if (ref.page_number) {
        citation += `, ${ref.page_number}`;
    }
    citation += ')';
    return citation;
}

// Atıf metnini sayfa numarasıyla oluştur
function getCitationTextWithPage(ref, pageNum) {
    // Birden fazla yazar var mı kontrol et (" & " ile ayrılmış)
    const hasMultipleAuthors = ref.author.includes(' & ');

    let authorPart;
    if (hasMultipleAuthors) {
        // İlk yazarın soyadını al ve "vd." ekle
        const firstAuthor = ref.author.split(' & ')[0].trim();
        const authorLast = firstAuthor.includes(',') ? firstAuthor.split(',')[0].trim() : firstAuthor.split(' ')[0];
        authorPart = `${authorLast} vd.`;
    } else {
        // Tek yazar
        authorPart = ref.author.includes(',') ? ref.author.split(',')[0].trim() : ref.author.split(' ')[0];
    }

    let citation = `(${authorPart}, ${ref.year}`;
    if (pageNum && pageNum.trim() !== '') {
        citation += `, ${pageNum.trim()}`;
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
    // Yazar listesini temizle
    authorsList = [];
    updateAuthorsList();
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

// Yazar ekleme sistemi
function addAuthor() {
    const lastnameInput = document.getElementById('author_lastname');
    const firstnameInput = document.getElementById('author_firstname');

    const lastname = lastnameInput.value.trim();
    const firstname = firstnameInput.value.trim();

    if (!lastname || !firstname) {
        if (window.showToast) {
            window.showToast('Lütfen hem soyadı hem adı girin', 'error', 2000);
        }
        return;
    }

    // "Soyadı, Ad" formatında ekle
    const fullName = `${lastname}, ${firstname}`;

    if (authorsList.includes(fullName)) {
        if (window.showToast) {
            window.showToast('Bu yazar zaten eklenmiş', 'warning', 2000);
        }
        return;
    }

    authorsList.push(fullName);
    updateAuthorsList();

    // Input alanlarını temizle
    lastnameInput.value = '';
    firstnameInput.value = '';
    lastnameInput.focus();
}

function removeAuthor(index) {
    authorsList.splice(index, 1);
    updateAuthorsList();
}

function updateAuthorsList() {
    const container = document.getElementById('authorsList');
    if (!container) return;

    if (authorsList.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = authorsList.map((author, index) => `
        <div class="dynamic-list-item">
            <span>${author}</span>
            <button type="button" class="remove-btn" onclick="removeAuthor(${index})" title="Kaldır">×</button>
        </div>
    `).join('');
}

// Enter tuşu ile ekleme
document.addEventListener('DOMContentLoaded', function() {
    const authorLastname = document.getElementById('author_lastname');
    const authorFirstname = document.getElementById('author_firstname');

    if (authorLastname && authorFirstname) {
        authorLastname.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                authorFirstname.focus();
            }
        });

        authorFirstname.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addAuthor();
            }
        });
    }
});

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
