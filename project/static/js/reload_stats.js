
function reload_stats(data, blocks) {
    for(i = 0; i < blocks.length; i++) {
        var name = `#${blocks[i]}`;
        var block = $(data).filter(name).html();
        $(name).html(block);
    }
}
