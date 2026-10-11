frappe.ui.form.on('RAG Document', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.upload_tai_lieu && frm.doc.status !== 'Processing') {
            frm.add_custom_button(__('Xử lý lại với OpenKB'), () => {
                frm.call('retry_openkb').then(() => frm.reload_doc());
            });
        }
        if (frm.doc.status === 'Processing') {
            frm.dashboard.set_headline(__('OpenKB đang xử lý nền. Tải lại để xem trạng thái.'));
        }
    }
});
