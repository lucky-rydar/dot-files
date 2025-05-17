-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

vim.opt.number = true
-- vim.opt.relativenumber = true

vim.o.expandtab = true       -- convert tabs to spaces
vim.o.shiftwidth = 4         -- number of spaces for each indentation
vim.o.tabstop = 4            -- number of spaces that a <Tab> in the file counts for
vim.o.softtabstop = 4        -- number of spaces inserted when pressing <Tab>

require("lazy").setup({
    -- File explorer
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },

    -- Theme
    "sainnhe/everforest",

    -- Integrated terminal
    "akinsho/toggleterm.nvim",

    -- LSP and completion
    "neovim/nvim-lspconfig",
    "hrsh7th/nvim-cmp",
    "hrsh7th/cmp-nvim-lsp",
    "L3MON4D3/LuaSnip",
    "saadparwaiz1/cmp_luasnip",

    -- Syntax highlighting
    "nvim-treesitter/nvim-treesitter",

    -- Status line
    "nvim-lualine/lualine.nvim",

    -- File finding / search
    "nvim-telescope/telescope.nvim",
    "nvim-lua/plenary.nvim",

    "akinsho/bufferline.nvim",
    version = "*",
    dependencies = { "nvim-tree/nvim-web-devicons" },

    "mason-org/mason.nvim",
    opts = {
        ensure_installer = {
            "clangd",
            "rust_analizer",
        }
    },
})

require("mason").setup()

vim.o.termguicolors = true
vim.g.everforest_background = "hard"  -- "medium" or "soft"
-- vim.g.everforest_background = "none"
vim.cmd([[colorscheme everforest]])

vim.cmd([[
  highlight Normal       guibg=NONE ctermbg=NONE
  highlight NormalNC     guibg=NONE ctermbg=NONE
  highlight SignColumn   guibg=NONE ctermbg=NONE
  highlight Pmenu        guibg=NONE ctermbg=NONE
  highlight PmenuSel     guibg=NONE ctermbg=NONE
  highlight PmenuSbar    guibg=NONE ctermbg=NONE
  highlight PmenuThumb   guibg=NONE ctermbg=NONE
  highlight FloatBorder  guibg=NONE ctermbg=NONE
  highlight NormalFloat  guibg=NONE ctermbg=NONE

  highlight NvimTreeNormal guibg=NONE
  highlight NvimTreeNormalNC guibg=NONE
  highlight NvimTreeStatusLine guibg=NONE
  highlight NvimTreeVertSplit guibg=NONE
]])

vim.cmd([[
  highlight NvimTreeNormal       guibg=NONE ctermbg=NONE
  highlight NvimTreeNormalNC     guibg=NONE ctermbg=NONE
  highlight NvimTreeStatusLine   guibg=NONE ctermbg=NONE
  highlight NvimTreeVertSplit    guibg=NONE ctermbg=NONE
  highlight NvimTreeWinSeparator guibg=NONE ctermbg=NONE
  highlight NvimTreeEndOfBuffer  guibg=NONE ctermbg=NONE
  highlight NvimTreeFolderName   guibg=NONE ctermbg=NONE
  highlight NvimTreeIndentMarker guibg=NONE ctermbg=NONE
  highlight NvimTreeGitDirty     guibg=NONE ctermbg=NONE
  highlight NvimTreeGitNew       guibg=NONE ctermbg=NONE
  highlight NvimTreeGitDeleted   guibg=NONE ctermbg=NONE
  highlight NvimTreeGitRenamed   guibg=NONE ctermbg=NONE
  highlight NvimTreeGitIgnored   guibg=NONE ctermbg=NONE
  highlight NvimTreeImageFile    guibg=NONE ctermbg=NONE
  highlight NvimTreeSymlink      guibg=NONE ctermbg=NONE
]])

vim.g.mapleader = " "

require("nvim-tree").setup()
vim.keymap.set("n", "<C-n>", ":NvimTreeToggle<CR>", { noremap = true, silent = true })
vim.keymap.set('n', '<leader><Tab>', function()
  require('nvim-tree.api').tree.change_root_to_node()
end, { noremap = true, silent = true })



require("toggleterm").setup()
vim.keymap.set("n", "<C-t>", ":ToggleTerm<CR>", { noremap = true, silent = true })
vim.keymap.set("t", "<C-x>", [[<C-\><C-n>:ToggleTerm<CR>]], { noremap = true, silent = true })

local cmp = require("cmp")
local luasnip = require("luasnip")

cmp.setup({
  snippet = {
    expand = function(args)
      luasnip.lsp_expand(args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ["<Tab>"] = cmp.mapping.select_next_item(),
    ["<S-Tab>"] = cmp.mapping.select_prev_item(),
    ["<CR>"] = cmp.mapping.confirm({ select = true }),
  }),
  sources = {
    { name = "nvim_lsp" },
    { name = "luasnip" },
  },
})

local actions = require("telescope.actions")
local action_state = require("telescope.actions.state")

vim.keymap.set("n", "<leader>ff", ":Telescope find_files<CR>")
vim.keymap.set("n", "<leader>fg", ":Telescope live_grep<CR>")
vim.keymap.set("n", "<leader>fb", ":Telescope buffers<CR>")

vim.keymap.set("n", "<leader>bn", ":enew<CR>")       -- new buffer
vim.keymap.set("n", "<leader>bd", ":bd<CR>")         -- delete buffer
vim.keymap.set("n", "<leader>bp", ":bprevious<CR>")  -- previous
vim.keymap.set("n", "<leader>bl", ":bnext<CR>")      -- next
vim.keymap.set("n", "<leader>bo", ":%bd|e#|bd#<CR>") -- leave only active

-- tab line at the top
vim.opt.termguicolors = true
-- vim.opt.showtabline = 1
-- vim.opt.hidden = true

require("bufferline").setup({})

vim.keymap.set("n", "<Tab>", "<cmd>BufferLineCycleNext<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<S-Tab>", "<cmd>BufferLineCyclePrev<CR>", { noremap = true, silent = true })

-- move between splits with Alt + h/j/k/l
vim.keymap.set("n", "<C-h>", "<C-w>h", { noremap = true })
vim.keymap.set("n", "<C-j>", "<C-w>j", { noremap = true })
vim.keymap.set("n", "<C-k>", "<C-w>k", { noremap = true })
vim.keymap.set("n", "<C-l>", "<C-w>l", { noremap = true })

-- horizontal and vertical splits
vim.keymap.set("n", "<leader>sv", ":vsplit<CR>", { noremap = true, silent = true }) -- vertical
vim.keymap.set("n", "<leader>sh", ":split<CR>", { noremap = true, silent = true })  -- horizontal
vim.keymap.set("n", "<leader>q", ":close<CR>", { noremap = true, silent = true }) -- close split

-- text manipulations
vim.keymap.set("n", "<A-j>", ":m .+1<CR>==", { noremap = true, silent = true })
vim.keymap.set("n", "<A-k>", ":m .-2<CR>==", { noremap = true, silent = true })
vim.keymap.set("v", "<A-j>", ":m '>+1<CR>gv=gv", { noremap = true, silent = true })
vim.keymap.set("v", "<A-k>", ":m '<-2<CR>gv=gv", { noremap = true, silent = true })

-- Select entire file with Ctrl+a
vim.keymap.set("n", "<C-a>", "ggVG", { noremap = true })

-- Yank to system clipboard
vim.keymap.set({ "n", "v" }, "<leader>y", [["+y]], { noremap = true })
vim.keymap.set("n", "<leader>Y", [["+Y]], { noremap = true })

-- Paste from system clipboard
vim.keymap.set({ "n", "v" }, "<leader>p", [["+p]], { noremap = true })

-- Delete without copying to register (safe delete)
vim.keymap.set({ "n", "v" }, "<leader>d", [["_d]], { noremap = true })

-- Replace currently selected text with paste (without yanking replaced text)
vim.keymap.set("v", "p", '"_dP', { noremap = true })

-- Easy navigation by word like Ctrl+Left/Right in VSCode (terminal must support it)
vim.keymap.set("i", "<C-Left>", "<C-\\><C-o>b", { noremap = true })
vim.keymap.set("i", "<C-Right>", "<C-\\><C-o>w", { noremap = true })

-- Quickly save
vim.keymap.set("n", "<C-s>", ":w<CR>", { noremap = true })

-- Quickly quit
vim.keymap.set("n", "<C-q>", ":q<CR>", { noremap = true })

-- Keep search result centered
vim.keymap.set("n", "n", "nzzzv", { noremap = true })
vim.keymap.set("n", "N", "Nzzzv", { noremap = true })
vim.keymap.set("n", "<Esc>", "<cmd>noh<CR><Esc>", { noremap = true, silent = true })

-- Keep cursor position when joining lines
vim.keymap.set("n", "J", "mzJ`z", { noremap = true })
